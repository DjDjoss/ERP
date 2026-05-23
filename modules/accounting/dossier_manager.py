from PySide6.QtWidgets import QMessageBox
from core.database import get_connection
import csv
import os
import requests
from modules.config import api_url

# Dossier courant (stocké en mémoire)
CURRENT_DOSSIER = None


# ---------------------------------------------------------
# 1) GESTION DU DOSSIER COURANT
# ---------------------------------------------------------

def set_current_dossier(dossier):
    global CURRENT_DOSSIER
    CURRENT_DOSSIER = dossier


def get_current_dossier():
    return CURRENT_DOSSIER


def update_window_title(window, dossier):
    """Met à jour le titre de l’ERP avec le nom du dossier ouvert."""
    if window is None:
        return

    if dossier:
        nom = dossier.get("nom_entreprise") or dossier.get("nom") or "Dossier sans nom"
        numero = dossier.get("num_dossier") or dossier.get("annee") or dossier.get("id", "")
        suffix = f" ({numero})" if numero else ""
        window.setWindowTitle(f"ERP Rosan - Dossier : {nom}{suffix}")
    else:
        window.setWindowTitle("ERP Rosan - Aucun dossier ouvert")


# ---------------------------------------------------------
# 2) IMPORT DU PCG LORS DE LA CRÉATION D’UN DOSSIER
# ---------------------------------------------------------

def import_pcg_for_dossier(dossier_id):
    """Importe le PCG général dans le dossier nouvellement créé."""
    conn = get_connection()
    cur = conn.cursor()

    pcg_file = "PCG_general.csv"  # À placer à la racine du projet

    if not os.path.exists(pcg_file):
        raise FileNotFoundError("Le fichier PCG_general.csv est introuvable.")

    with open(pcg_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # sauter l’en-tête

        for row in reader:
            numero = row[0]
            intitule = row[1]
            type_compte = row[2]

            cur.execute("""
                INSERT INTO pcg (dossier_id, numero, intitule, type)
                VALUES (?, ?, ?, ?)
            """, (dossier_id, numero, intitule, type_compte))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 3) CRÉATION DES JOURNAUX STANDARDS
# ---------------------------------------------------------

JOURNAUX_STANDARD = [
    ("AN", "À nouveau"),
    ("ACH", "Achats"),
    ("VTE", "Ventes"),
    ("BD", "BRED"),
    ("BP", "Banque Postale"),
    ("CA", "Crédit Agricole"),
    ("CE", "Caisse d'Épargne"),
    ("CM", "Crédit Mutuel"),
    ("BNP", "BNP Paribas"),
    ("CAI", "Caisse"),
    ("OP", "Opérations diverses"),
    ("IMO", "Immobilisations"),
    ("ODE", "OD Expert / CAC"),
    ("ODR", "OD de révision")
]


def create_standard_journaux(dossier_id):
    conn = get_connection()
    cur = conn.cursor()

    for code, libelle in JOURNAUX_STANDARD:
        cur.execute("""
            INSERT INTO journaux (dossier_id, code, libelle)
            VALUES (?, ?, ?)
        """, (dossier_id, code, libelle))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 4) SUPPRESSION D’UN DOSSIER (3 ALERTES)
# ---------------------------------------------------------

def delete_dossier_with_alerts(parent_widget):
    dossier = get_current_dossier()

    if dossier is None:
        QMessageBox.warning(parent_widget, "Erreur", "Aucun dossier n’est ouvert.")
        return

    dossier_id = dossier.get("id")
    nom = dossier.get("nom_entreprise") or dossier.get("nom") or "ce dossier"

    # Alerte 1
    r1 = QMessageBox.question(
        parent_widget,
        "Confirmation",
        f"Voulez-vous vraiment supprimer le dossier « {nom} » ?"
    )
    if r1 != QMessageBox.Yes:
        return

    # Alerte 2
    r2 = QMessageBox.question(
        parent_widget,
        "Attention",
        "Cette action est irréversible. Toutes les données seront perdues.\nContinuer ?"
    )
    if r2 != QMessageBox.Yes:
        return

    # Alerte 3
    r3 = QMessageBox.question(
        parent_widget,
        "Dernière confirmation",
        "Êtes-vous ABSOLUMENT sûr ?"
    )
    if r3 != QMessageBox.Yes:
        return

    if dossier_id is None:
        QMessageBox.critical(parent_widget, "Erreur", "Identifiant dossier introuvable.")
        return

    try:
        response = requests.delete(api_url(f"/dossiers/{dossier_id}"), timeout=10)
        response.raise_for_status()
    except Exception as exc:
        QMessageBox.critical(parent_widget, "Erreur", f"Suppression impossible : {exc}")
        return

    set_current_dossier(None)

    QMessageBox.information(parent_widget, "Succès", "Dossier supprimé avec succès.")


# ---------------------------------------------------------
# 5) CRÉATION D’UN DOSSIER (PCG + JOURNAUX)
# ---------------------------------------------------------

def create_dossier_in_db(nom, annee):
    """Crée un dossier + PCG + journaux standards."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO dossiers (nom, annee)
        VALUES (?, ?)
    """, (nom, annee))

    dossier_id = cur.lastrowid
    conn.commit()
    conn.close()

    # Import PCG
    import_pcg_for_dossier(dossier_id)

    # Journaux standards
    create_standard_journaux(dossier_id)

    return dossier_id
