from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QHBoxLayout, QMessageBox, QWidget, QScrollArea,
    QSizePolicy, QLayout
)

from PySide6.QtCore import Qt, QSize
import re
import json
import os
from pathlib import Path
import requests
from modules.config import api_url



def compute_tva_intracom_from_siren(siren: str) -> str:
    if not re.fullmatch(r"\d{9}", siren):
        return ""
    n = int(siren)
    cle = (12 + 3 * (n % 97)) % 97
    return f"FR{cle:02d}{siren}"

DEPARTEMENT_TO_REGION = {
    "01": "Auvergne-Rhône-Alpes", "02": "Hauts-de-France", "03": "Auvergne-Rhône-Alpes",
    "04": "Provence-Alpes-Côte d’Azur", "05": "Provence-Alpes-Côte d’Azur",
    "06": "Provence-Alpes-Côte d’Azur", "07": "Auvergne-Rhône-Alpes",
    "08": "Grand Est", "09": "Occitanie", "10": "Grand Est", "11": "Occitanie",
    "12": "Occitanie", "13": "Provence-Alpes-Côte d’Azur", "14": "Normandie",
    "15": "Auvergne-Rhône-Alpes", "16": "Nouvelle-Aquitaine", "17": "Nouvelle-Aquitaine",
    "18": "Centre-Val de Loire", "19": "Nouvelle-Aquitaine",
    "2A": "Corse", "2B": "Corse",
    "21": "Bourgogne-Franche-Comté", "22": "Bretagne", "23": "Nouvelle-Aquitaine",
    "24": "Nouvelle-Aquitaine", "25": "Bourgogne-Franche-Comté",
    "26": "Auvergne-Rhône-Alpes", "27": "Normandie", "28": "Centre-Val de Loire",
    "29": "Bretagne", "30": "Occitanie", "31": "Occitanie", "32": "Occitanie",
    "33": "Nouvelle-Aquitaine", "34": "Occitanie", "35": "Bretagne",
    "36": "Centre-Val de Loire", "37": "Centre-Val de Loire",
    "38": "Auvergne-Rhône-Alpes", "39": "Bourgogne-Franche-Comté",
    "40": "Nouvelle-Aquitaine", "41": "Centre-Val de Loire",
    "42": "Auvergne-Rhône-Alpes", "43": "Auvergne-Rhône-Alpes",
    "44": "Pays de la Loire", "45": "Centre-Val de Loire",
    "46": "Occitanie", "47": "Nouvelle-Aquitaine", "48": "Occitanie",
    "49": "Pays de la Loire", "50": "Normandie", "51": "Grand Est",
    "52": "Grand Est", "53": "Pays de la Loire", "54": "Grand Est",
    "55": "Grand Est", "56": "Bretagne", "57": "Grand Est",
    "58": "Bourgogne-Franche-Comté", "59": "Hauts-de-France",
    "60": "Hauts-de-France", "61": "Normandie", "62": "Hauts-de-France",
    "63": "Auvergne-Rhône-Alpes", "64": "Nouvelle-Aquitaine",
    "65": "Occitanie", "66": "Occitanie", "67": "Grand Est",
    "68": "Grand Est", "69": "Auvergne-Rhône-Alpes",
    "70": "Bourgogne-Franche-Comté", "71": "Bourgogne-Franche-Comté",
    "72": "Pays de la Loire", "73": "Auvergne-Rhône-Alpes",
    "74": "Auvergne-Rhône-Alpes", "75": "Île-de-France",
    "76": "Normandie", "77": "Île-de-France", "78": "Île-de-France",
    "79": "Nouvelle-Aquitaine", "80": "Hauts-de-France",
    "81": "Occitanie", "82": "Occitanie", "83": "Provence-Alpes-Côte d’Azur",
    "84": "Provence-Alpes-Côte d’Azur", "85": "Pays de la Loire",
    "86": "Nouvelle-Aquitaine", "87": "Nouvelle-Aquitaine",
    "88": "Grand Est", "89": "Bourgogne-Franche-Comté",
    "90": "Bourgogne-Franche-Comté", "91": "Île-de-France",
    "92": "Île-de-France", "93": "Île-de-France", "94": "Île-de-France",
    "95": "Île-de-France",
    "971": "Guadeloupe", "972": "Martinique", "973": "Guyane",
    "974": "Réunion", "976": "Mayotte",
    "975": "Saint-Pierre-et-Miquelon", "984": "TAAF",
    "986": "Wallis-et-Futuna", "987": "Polynésie française",
    "988": "Nouvelle-Calédonie", "989": "Clipperton",
}


NAF_CODES = {}
naf_path = Path(os.path.join(os.path.dirname(__file__), "data", "naf_codes.json"))
if naf_path.exists():
    with open(naf_path, "r", encoding="utf-8") as f:
        NAF_CODES = json.load(f)


class DossierCreateDialog(QDialog):
    def __init__(self, parent=None, dossier_id=None):
        super().__init__(parent)  # OBLIGATOIRE

        self.dossier_id = dossier_id  # MODE CRÉATION / MODIFICATION

        self.setWindowTitle(
            "Création d’un dossier" if dossier_id is None else "Modification d’un dossier"
        )
        self.setMinimumSize(QSize(900, 800))
        self.resize(900, 1000)
        self.setModal(True)

        self.apply_styles()
        self.build_ui()
        self.center_on_screen()

        self.cp_dict = self.load_postal_codes()
        self.cp.textChanged.connect(self.on_cp_changed)

        if self.dossier_id is not None:
            self.load_dossier_for_edit()

    def apply_styles(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                margin-top: 14px;
                border: 1px solid #888;
                border-radius: 6px;
                padding: 12px;
            }
            QLabel {
                color: black;
                font-size: 13px;
            }
            QLineEdit, QComboBox {
                font-size: 13px;
                color: #0055CC;
                font-weight: 500;
            }
        """)

    def build_ui(self):
        # =========================================================
        # BLOC 1 — Initialisation de la fenêtre
        # (Hauteur OK, largeur auto sans fixe)
        # =========================================================
        screen = self.screen().availableGeometry()

        # Hauteur : on garde ton comportement d’origine
        self.resize(int(screen.width() * 0.9), int(screen.height() * 0.9))

        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Boutons en haut (centrés)
        content_layout.addLayout(self.build_buttons())


        # =========================================================
        # BLOC 2 — Widgets JURIDIQUES ÉTABLISSEMENT
        # =========================================================
        self.label_forme = QLabel("Forme juridique")
        self.label_nom_commercial = QLabel("Nom commercial")
        self.label_frp = QLabel("FRP")
        self.label_cdi = QLabel("CDI")
        self.label_service = QLabel("Service")
        self.label_rc = QLabel("N° R.C")
        self.label_naf = QLabel("APE / NAF")
        self.label_naf_def = QLabel("Définition APE / NAF")
        self.label_capital = QLabel("Capital social")
        self.label_parts = QLabel("Nombre de parts")
        self.label_date_creation = QLabel("Date de création")
        self.label_date_cloture = QLabel("Date de clôture")

        self.forme = QComboBox(); self.forme.addItems(["SARL","EURL","SAS","SASU","SCI","EI","Autre"])
        self.nom_commercial = QLineEdit()
        self.frp = QComboBox(); self.frp.addItems(["Oui","Non"])
        self.cdi = QComboBox(); self.cdi.addItems(["Oui","Non"])
        self.service = QComboBox(); self.service.addItems(["Direction","Comptabilité","RH","Commercial","Production","Autre"])
        self.rc = QLineEdit()
        self.naf = QLineEdit()
        self.naf_def = QLineEdit()
        self.capital = QLineEdit()
        self.parts = QLineEdit()
        self.date_creation = QLineEdit()
        self.date_cloture = QLineEdit()

        # =========================================================
        # BLOC 3 — Widgets JURIDIQUES SIÈGE
        # =========================================================
        self.siege_label_forme = QLabel("Forme juridique")
        self.siege_label_nom_commercial = QLabel("Nom commercial")
        self.siege_label_frp = QLabel("FRP")
        self.siege_label_cdi = QLabel("CDI")
        self.siege_label_service = QLabel("Service")
        self.siege_label_rc = QLabel("N° R.C")
        self.siege_label_naf = QLabel("APE / NAF")
        self.siege_label_naf_def = QLabel("Définition APE / NAF")
        self.siege_label_capital = QLabel("Capital social")
        self.siege_label_parts = QLabel("Nombre de parts")
        self.siege_label_date_creation = QLabel("Date de création")
        self.siege_label_date_cloture = QLabel("Date de clôture")

        self.siege_forme = QComboBox(); self.siege_forme.addItems(["SARL","EURL","SAS","SASU","SCI","EI","Autre"])
        self.siege_nom_commercial = QLineEdit()
        self.siege_frp = QComboBox(); self.siege_frp.addItems(["Oui","Non"])
        self.siege_cdi = QComboBox(); self.siege_cdi.addItems(["Oui","Non"])
        self.siege_service = QComboBox(); self.siege_service.addItems(["Direction","Comptabilité","RH","Commercial","Production","Autre"])
        self.siege_rc = QLineEdit()
        self.siege_naf = QLineEdit()
        self.siege_naf_def = QLineEdit()
        self.siege_capital = QLineEdit()
        self.siege_parts = QLineEdit()
        self.siege_date_creation = QLineEdit()
        self.siege_date_cloture = QLineEdit()

        # =========================================================
        # BLOC 4 — Alignement des largeurs
        # =========================================================
        LABEL_WIDTH = 160
        FIELD_WIDTH = 250

        for lbl in [
            self.label_forme, self.label_nom_commercial, self.label_frp, self.label_cdi,
            self.label_service, self.label_rc, self.label_naf, self.label_naf_def,
            self.label_capital, self.label_parts, self.label_date_creation, self.label_date_cloture,
            self.siege_label_forme, self.siege_label_nom_commercial, self.siege_label_frp,
            self.siege_label_cdi, self.siege_label_service, self.siege_label_rc,
            self.siege_label_naf, self.siege_label_naf_def, self.siege_label_capital,
            self.siege_label_parts, self.siege_label_date_creation, self.siege_label_date_cloture,
        ]:
            lbl.setFixedWidth(LABEL_WIDTH)

        for fld in [
            self.forme, self.nom_commercial, self.frp, self.cdi, self.service, self.rc,
            self.naf, self.naf_def, self.capital, self.parts, self.date_creation, self.date_cloture,
            self.siege_forme, self.siege_nom_commercial, self.siege_frp, self.siege_cdi,
            self.siege_service, self.siege_rc, self.siege_naf, self.siege_naf_def,
            self.siege_capital, self.siege_parts, self.siege_date_creation, self.siege_date_cloture,
        ]:
            fld.setFixedWidth(FIELD_WIDTH)

        # =========================================================
        # BLOC 5 — Pavés ÉTABLISSEMENT
        # =========================================================
        etab_widget = QWidget()
        etab_layout = QVBoxLayout(etab_widget)
        etab_layout.addWidget(self.build_identite_box())
        etab_layout.addWidget(self.build_coordonnees_box())
        etab_layout.addWidget(self.build_juridique_box())
        etab_layout.addWidget(self.build_fiscalite_box())
        etab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # =========================================================
        # BLOC 6 — Pavés SIÈGE
        # =========================================================
        siege_widget = QWidget()
        siege_layout = QVBoxLayout(siege_widget)
        siege_layout.addWidget(self.build_siege_identite_box())
        siege_layout.addWidget(self.build_siege_coordonnees_box())
        siege_layout.addWidget(self.build_siege_juridique_box())
        siege_layout.addWidget(self.build_siege_fiscalite_box())
        siege_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # =========================================================
        # BLOC 7 — Double colonne ÉTABLISSEMENT | SIÈGE
        # =========================================================
        hbox = QHBoxLayout()
        hbox.addWidget(etab_widget)
        hbox.addWidget(siege_widget)

        # Répartition 50/50
        hbox.setStretch(0, 1)
        hbox.setStretch(1, 1)

        # 👉 Largeur dictée par les 4 colonnes
        hbox.setSizeConstraint(QLayout.SetMinimumSize)

        content_layout.addLayout(hbox)

        # =========================================================
        # BLOC 8 — Boutons
        # =========================================================
        content_layout.addLayout(self.build_buttons())

        # =========================================================
        # BLOC 9 — Scroll vertical uniquement + Layout final
        # =========================================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

        # 👉 Largeur auto, hauteur intacte
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)


    def build_identite_box(self):
        box = QGroupBox("Identité de l’Entreprise - Siren - Siret - Tva - Nom")
        grid = QGridLayout()

        self.siren = QLineEdit()
        self.siren.setMaxLength(9)

        self.nic = QLineEdit()
        self.nic.setMaxLength(5)
        self.nic.setInputMask("00000")

        self.siret = QLineEdit()
        self.siret.setReadOnly(True)

        self.tva = QLineEdit()
        self.tva.setReadOnly(True)

        self.nom_entreprise = QLineEdit()
        self.nom_entreprise.textChanged.connect(self.on_nom_entreprise_changed)

        self.btn_pappers = QPushButton("🔍 Remplir automatiquement")
        self.btn_pappers.clicked.connect(self.on_pappers_clicked)

        self.siren.textChanged.connect(self.update_siret_tva)
        self.nic.textChanged.connect(self.update_siret_tva)

        grid.addWidget(QLabel("SIREN"), 0, 0)
        grid.addWidget(self.siren, 0, 1)

        label_nic = QLabel("NIC")
        label_nic.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(label_nic, 0, 2)
        grid.addWidget(self.nic, 0, 3)

        grid.addWidget(QLabel("SIRET"), 1, 0)
        grid.addWidget(self.siret, 1, 1)

        grid.addWidget(QLabel("TVA Intracom"), 1, 2)
        grid.addWidget(self.tva, 1, 3)

        grid.addWidget(QLabel("Nom de l’entreprise"), 2, 0)
        grid.addWidget(self.nom_entreprise, 2, 1, 1, 3)

        grid.addWidget(self.btn_pappers, 3, 0, 1, 4, alignment=Qt.AlignCenter)

        box.setLayout(grid)
        return box

    # ---------------------------------------------------------
    # PAVÉ 2 — COORDONNÉES (corrigé)
    # ---------------------------------------------------------
    def build_coordonnees_box(self):
        box = QGroupBox("Adresses et Contacts")
        grid = QGridLayout()

        # ---------------------------------------------------------
        # TITRES SUR LA MÊME LIGNE
        # ---------------------------------------------------------
        label_coord = QLabel("Coordonnées")
        label_coord.setStyleSheet("font-weight: bold; font-size: 15px;")

        label_contact = QLabel("Contacts")
        label_contact.setStyleSheet("font-weight: bold; font-size: 15px;")

        grid.addWidget(label_coord, 0, 0, 1, 2)   # colonne gauche
        grid.addWidget(label_contact, 0, 2, 1, 2, alignment=Qt.AlignRight)  # colonne droite

        # ---------------------------------------------------------
        # COLONNE GAUCHE — ADRESSE
        # ---------------------------------------------------------
        self.adresse1 = QLineEdit()
        self.adresse2 = QLineEdit()
        self.complement = QLineEdit()
        self.cp = QLineEdit()
        self.ville = QLineEdit()

        self.region = QComboBox()
        self.region.addItems([
            "Guadeloupe", "Martinique", "Guyane", "Réunion", "Mayotte",
            "Île-de-France", "Corse", "Nouvelle-Aquitaine", "Occitanie",
            "Provence-Alpes-Côte d’Azur", "Auvergne-Rhône-Alpes",
            "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire",
            "Grand Est", "Hauts-de-France", "Normandie", "Pays de la Loire",
            "TAAF", "Wallis-et-Futuna", "Polynésie française",
            "Nouvelle-Calédonie", "Saint-Pierre-et-Miquelon", "Clipperton"
        ])

        self.pays = QComboBox()
        self.pays.addItems(["France", "Belgique", "Suisse", "Luxembourg"])

        # ---------------------------------------------------------
        # COLONNE DROITE — CONTACT
        # ---------------------------------------------------------
        self.tel_fixe = QLineEdit()
        self.tel_port = QLineEdit()
        self.email = QLineEdit()
        self.web = QLineEdit()
        self.resp_nom = QLineEdit()
        self.resp_tel = QLineEdit()
        self.resp_email = QLineEdit()

        # ---------------------------------------------------------
        # LIGNES DE LA GRILLE
        # ---------------------------------------------------------
        row = 1

        grid.addWidget(QLabel("Adresse (ligne 1)"), row, 0)
        grid.addWidget(self.adresse1, row, 1)
        grid.addWidget(QLabel("📞 Téléphone fixe"), row, 2)
        grid.addWidget(self.tel_fixe, row, 3)
        row += 1

        grid.addWidget(QLabel("Adresse (ligne 2)"), row, 0)
        grid.addWidget(self.adresse2, row, 1)
        grid.addWidget(QLabel("📱 Portable"), row, 2)
        grid.addWidget(self.tel_port, row, 3)
        row += 1

        grid.addWidget(QLabel("Complément"), row, 0)
        grid.addWidget(self.complement, row, 1)
        grid.addWidget(QLabel("✉️ Email"), row, 2)
        grid.addWidget(self.email, row, 3)
        row += 1

        grid.addWidget(QLabel("Code postal"), row, 0)
        grid.addWidget(self.cp, row, 1)
        grid.addWidget(QLabel("🌐 Site web"), row, 2)
        grid.addWidget(self.web, row, 3)
        row += 1

        grid.addWidget(QLabel("Ville"), row, 0)
        grid.addWidget(self.ville, row, 1)
        grid.addWidget(QLabel("👤 Responsable"), row, 2)
        grid.addWidget(self.resp_nom, row, 3)
        row += 1

        grid.addWidget(QLabel("Région"), row, 0)
        grid.addWidget(self.region, row, 1)
        grid.addWidget(QLabel("📞 Téléphone Resp."), row, 2)
        grid.addWidget(self.resp_tel, row, 3)
        row += 1

        grid.addWidget(QLabel("Pays"), row, 0)
        grid.addWidget(self.pays, row, 1)
        grid.addWidget(QLabel("✉️ Email Resp."), row, 2)
        grid.addWidget(self.resp_email, row, 3)

        box.setLayout(grid)
        return box

    # ---------------------------------------------------------
    # PAVÉ 3 — INFORMATIONS JURIDIQUES (corrigé)
    # ---------------------------------------------------------
    def build_juridique_box(self):
        box = QGroupBox("Informations juridiques — Établissement")
        grid = QGridLayout()

        # Ligne 1
        grid.addWidget(self.label_forme,          0, 0)
        grid.addWidget(self.forme,                0, 1)
        grid.addWidget(self.label_nom_commercial, 0, 2)
        grid.addWidget(self.nom_commercial,       0, 3)

        # Ligne 2
        grid.addWidget(self.label_frp,            1, 0)
        grid.addWidget(self.frp,                  1, 1)
        grid.addWidget(self.label_cdi,            1, 2)
        grid.addWidget(self.cdi,                  1, 3)

        # Ligne 3
        grid.addWidget(self.label_service,        2, 0)
        grid.addWidget(self.service,              2, 1)
        grid.addWidget(self.label_rc,             2, 2)
        grid.addWidget(self.rc,                   2, 3)

        # Ligne 4
        grid.addWidget(self.label_naf,            3, 0)
        grid.addWidget(self.naf,                  3, 1)
        grid.addWidget(self.label_naf_def,        3, 2)
        grid.addWidget(self.naf_def,              3, 3)

        # Ligne 5
        grid.addWidget(self.label_capital,        4, 0)
        grid.addWidget(self.capital,              4, 1)
        grid.addWidget(self.label_parts,          4, 2)
        grid.addWidget(self.parts,                4, 3)

        # Ligne 6
        grid.addWidget(self.label_date_creation,  5, 0)
        grid.addWidget(self.date_creation,        5, 1)
        grid.addWidget(self.label_date_cloture,   5, 2)
        grid.addWidget(self.date_cloture,         5, 3)

        box.setLayout(grid)
        return box

    # ---------------------------------------------------------
    # LOGIQUE : NAF (auto‑complétion intelligente)
    # ---------------------------------------------------------
    def update_naf_definition(self):
        naf = self.naf.text().strip().upper()
        self.naf.setText(naf)

        if naf == "":
            self.naf_def.clear()
            self.naf_def.setProperty("error", False)
            self.naf_def.style().unpolish(self.naf_def)
            self.naf_def.style().polish(self.naf_def)
            return

        if naf in NAF_CODES:
            self.naf_def.setText(NAF_CODES[naf])
            self.naf_def.setProperty("error", False)
        else:
            matches = [code for code in NAF_CODES.keys() if code.startswith(naf)]

            if len(matches) == 1:
                self.naf_def.setText(NAF_CODES[matches[0]])
                self.naf_def.setProperty("error", False)
            elif len(matches) > 1:
                self.naf_def.setText(f"{len(matches)} codes possibles…")
                self.naf_def.setProperty("error", False)
            else:
                self.naf_def.setText("Code NAF inconnu (non bloquant).")
                self.naf_def.setProperty("error", True)

        self.naf_def.style().unpolish(self.naf_def)
        self.naf_def.style().polish(self.naf_def)

    # ---------------------------------------------------------
    # PAVÉ 4 — RÉGIME FISCAL & TVA
    # ---------------------------------------------------------
    def build_fiscalite_box(self):
        box = QGroupBox("Régime Fiscal & TVA")
        grid = QGridLayout()

        self.type_dossier = QComboBox()
        self.type_dossier.addItems(["BIC", "BNC", "BA"])

        self.regime_fiscal = QComboBox()
        self.regime_fiscal.addItems(["Réel simplifié", "Réel normal", "Micro"])

        self.imposition = QComboBox()
        self.imposition.addItems(["IS", "IR"])

        self.regime_tva = QComboBox()
        self.regime_tva.addItems(["Réel simplifié", "Réel normal", "Franchise en base"])

        self.tva2 = QLineEdit()
        self.tva2.setReadOnly(True)

        grid.addWidget(QLabel("Type de dossier"), 0, 0)
        grid.addWidget(self.type_dossier, 0, 1)

        grid.addWidget(QLabel("Régime fiscal"), 1, 0)
        grid.addWidget(self.regime_fiscal, 1, 1)

        grid.addWidget(QLabel("Imposition"), 2, 0)
        grid.addWidget(self.imposition, 2, 1)

        grid.addWidget(QLabel("Régime TVA"), 3, 0)
        grid.addWidget(self.regime_tva, 3, 1)

        grid.addWidget(QLabel("TVA Intracom"), 4, 0)
        grid.addWidget(self.tva2, 4, 1)

        box.setLayout(grid)
        return box

    # ---------------------------------------------------------
    # BOUTONS
    # ---------------------------------------------------------
    def build_buttons(self):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        self.btn_save = QPushButton("ENREGISTRER")
        self.btn_save_quit = QPushButton("ENREGISTRER ET QUITTER")
        self.btn_cancel = QPushButton("ANNULER")

        # --- Styles professionnels, couleurs adoucies ---
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;   /* Bleu doux */
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        """)

        self.btn_save_quit.setStyleSheet("""
            QPushButton {
                background-color: #66BB6A;   /* Vert doux */
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4E9E55;
            }
        """)

        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #EF5350;   /* Rouge doux */
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D84341;
            }
        """)

        # --- Ajout des boutons ---
        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_save_quit)
        layout.addWidget(self.btn_cancel)

        # --- Connexions ---
        self.btn_save.clicked.connect(self.on_save_clicked)
        self.btn_save_quit.clicked.connect(self.on_save_quit_clicked)
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)

        return layout


    # ---------------------------------------------------------
    # LOGIQUE : SIRET + TVA
    # ---------------------------------------------------------
    def update_siret_tva(self):
        siren = self.siren.text().strip()
        nic = self.nic.text().strip()

        if re.fullmatch(r"\d{9}", siren) and re.fullmatch(r"\d{5}", nic):
            self.siret.setText(siren + nic)
            tva = compute_tva_intracom_from_siren(siren)
            self.tva.setText(tva)
            self.tva2.setText(tva)
        else:
            self.siret.clear()
            self.tva.clear()
            self.tva2.clear()


    def update_siege_siret_tva(self):
        siren = self.siege_siren.text().strip()
        nic = self.siege_nic.text().strip()

        if re.fullmatch(r"\d{9}", siren) and re.fullmatch(r"\d{5}", nic):
            self.siege_siret.setText(siren + nic)
            tva = compute_tva_intracom_from_siren(siren)
            self.siege_tva.setText(tva)
            self.siege_tva2.setText(tva)
        else:
            self.siege_siret.clear()
            self.siege_tva.clear()
            self.siege_tva2.clear()

    # ---------------------------------------------------------
    # REMPLISSAGE ETABLISSEMENT (PAPPERS)
    # ---------------------------------------------------------
    def fill_etablissement_from_pappers(self, etab, siege=None):
        # ---------------------------------------------------------
        # NOM COMMERCIAL (établissement)
        # ---------------------------------------------------------
        nom_com = etab.get("nom_commercial") or etab.get("enseigne") or ""
        if nom_com in (None, "None"):
            nom_com = ""

        # ---------------------------------------------------------
        # DÉNOMINATION (uniquement pour le nom final)
        # ---------------------------------------------------------
        denomination = ""
        if siege:
            denomination = siege.get("denomination") or ""
            if denomination in (None, "None"):
                denomination = ""

        # ---------------------------------------------------------
        # FORMATION DU NOM DE L’ENTREPRISE (ÉTABLISSEMENT)
        # nom_commercial + denomination
        # ---------------------------------------------------------
        parts = []

        if nom_com.strip():
            parts.append(nom_com.strip())

        if denomination.strip():
            parts.append(denomination.strip())

        nom_final = " ".join(parts).strip()

        # ---------------------------------------------------------
        # SI VIDE → "A saisir" en rouge
        # ---------------------------------------------------------
        if not nom_final:
            self.nom_entreprise.setText("A saisir")
            self.nom_entreprise.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.nom_entreprise.setText(nom_final)
            self.nom_entreprise.setStyleSheet("")  # reset style
            self.mark_autofilled(self.nom_entreprise)

        # ---------------------------------------------------------
        # NOM COMMERCIAL (champ séparé)
        # ---------------------------------------------------------
        self.nom_commercial.setText(nom_com)

        # ---------------------------------------------------------
        # ADRESSE (ÉTABLISSEMENT)
        # ---------------------------------------------------------
        self.adresse1.setText(etab.get("adresse_ligne_1", ""))
        self.adresse2.setText(etab.get("adresse_ligne_2", ""))
        self.complement.setText(etab.get("complement_adresse", ""))
        self.cp.setText(etab.get("code_postal", ""))
        self.ville.setText(etab.get("ville", ""))

        pays = etab.get("pays", "France")
        idx = self.pays.findText(pays)
        if idx >= 0:
            self.pays.setCurrentIndex(idx)

        self.on_cp_changed()

        # ---------------------------------------------------------
        # JURIDIQUE — PRO (ÉTABLISSEMENT)
        # ---------------------------------------------------------
        self.forme.setCurrentText(etab.get("forme_juridique", ""))
        self.frp.setCurrentText(etab.get("frp", ""))
        self.cdi.setCurrentText(etab.get("cdi", ""))
        self.service.setCurrentText(etab.get("service", ""))

        self.rc.setText(etab.get("numero_rcs", ""))
        self.naf.setText(etab.get("code_naf_2025") or etab.get("code_naf") or "")
        self.naf_def.setText(etab.get("libelle_code_naf", ""))

        self.capital.setText(str(etab.get("capital", "")))
        self.parts.setText(str(etab.get("parts", "")))
        self.date_creation.setText(etab.get("date_de_creation", ""))
        self.date_cloture.setText(etab.get("date_cloture_exercice", ""))

        # ---------------------------------------------------------
        # TVA (ÉTABLISSEMENT)
        # ---------------------------------------------------------
        tva = etab.get("numero_tva_intracommunautaire", "")
        self.tva.setText(tva)
        self.tva2.setText(tva)

    # ---------------------------------------------------------
    # REMPLISSAGE SIEGE (PAPPERS)
    # ---------------------------------------------------------
    def fill_siege_from_pappers(self, siege):
        # IDENTITÉ
        self.siege_siren.setText(siege.get("siren", ""))
        self.siege_nic.setText(siege.get("nic", ""))
        self.siege_siret.setText(siege.get("siret", ""))
        self.siege_tva.setText(siege.get("numero_tva_intracommunautaire", ""))

        nom = siege.get("nom_commercial") or siege.get("enseigne") or ""
        self.siege_nom_entreprise.setText(nom)
        self.siege_nom_commercial.setText(nom)

        # ADRESSE
        self.siege_adresse1.setText(siege.get("adresse_ligne_1", ""))
        self.siege_adresse2.setText(siege.get("adresse_ligne_2", ""))
        self.siege_complement.setText(siege.get("complement_adresse", ""))
        self.siege_cp.setText(siege.get("code_postal", ""))
        self.siege_ville.setText(siege.get("ville", ""))

        pays = siege.get("pays", "France")
        idx = self.siege_pays.findText(pays)
        if idx >= 0:
            self.siege_pays.setCurrentIndex(idx)

        # JURIDIQUE — SIÈGE
        self.siege_forme.setCurrentText(siege.get("forme_juridique", ""))
        self.siege_frp.setCurrentText(siege.get("frp", ""))
        self.siege_cdi.setCurrentText(siege.get("cdi", ""))
        self.siege_service.setCurrentText(siege.get("service", ""))

        self.siege_rc.setText(siege.get("numero_rcs", ""))
        self.siege_naf.setText(siege.get("code_naf_2025") or siege.get("code_naf") or "")
        self.siege_naf_def.setText(siege.get("libelle_code_naf", ""))
        self.siege_capital.setText(str(siege.get("capital", "")))
        self.siege_parts.setText(str(siege.get("parts", "")))
        self.siege_date_creation.setText(siege.get("date_de_creation", ""))
        self.siege_date_cloture.setText(siege.get("date_cloture_exercice", ""))

    def on_nom_entreprise_changed(self, text):
        # Si l'utilisateur modifie le champ et que ce n'est plus "A saisir"
        if text.strip() and text.strip().lower() != "a saisir":
            # Style bleu (comme les champs auto-remplis)
            self.nom_entreprise.setStyleSheet("color: #0078d4; font-weight: normal;")

    # ---------------------------------------------------------
    # LOGIQUE : CHARGEMENT CP → VILLE + RÉGION + PAYS
    # ---------------------------------------------------------
    def load_postal_codes(self):
        path = os.path.join(os.path.dirname(__file__), "data", "postal_codes_fr.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def on_cp_changed(self):
        cp = self.cp.text().strip()

        if cp in self.cp_dict:
            self.ville.setText(self.cp_dict[cp])
        else:
            self.ville.clear()

        region = None

        if len(cp) == 5 and cp[:3] in DEPARTEMENT_TO_REGION:
            region = DEPARTEMENT_TO_REGION[cp[:3]]
        elif len(cp) == 5 and cp[:2] in DEPARTEMENT_TO_REGION:
            region = DEPARTEMENT_TO_REGION[cp[:2]]

        if region:
            idx = self.region.findText(region)
            if idx >= 0:
                self.region.setCurrentIndex(idx)

        idx = self.pays.findText("France")
        if idx >= 0:
            self.pays.setCurrentIndex(idx)

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------
    def validate_required(self):
        ok = True

        self.siren.setProperty("error", False)
        self.nom_entreprise.setProperty("error", False)

        siren = self.siren.text().strip()
        if siren and not re.fullmatch(r"\d{9}", siren):
            self.siren.setProperty("error", True)
            ok = False

        if self.nom_entreprise.text().strip() == "":
            self.nom_entreprise.setProperty("error", True)
            ok = False

        self.siren.style().unpolish(self.siren)
        self.siren.style().polish(self.siren)
        self.nom_entreprise.style().unpolish(self.nom_entreprise)
        self.nom_entreprise.style().polish(self.nom_entreprise)

        return ok

    # ---------------------------------------------------------
    # BOUTON : REMPLIR AUTOMATIQUEMENT (PAPPERS)
    # ---------------------------------------------------------
    def on_pappers_clicked(self):
        siret = self.siret.text().strip()

        if len(siret) != 14 or not siret.isdigit():
            QMessageBox.warning(self, "Erreur", "Veuillez saisir un SIRET valide (14 chiffres).")
            return

        try:
            url = api_url(f"/dossiers/from-pappers/{siret}")
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                QMessageBox.warning(self, "Erreur API", response.text)
                return

            p = response.json()
            if not isinstance(p, dict):
                QMessageBox.warning(self, "Erreur", "Réponse API invalide.")
                return

            # Compatibilité: accepte l'ancien et le nouveau format backend.
            if p.get("status") == "success":
                payload = p.get("data", {})
            else:
                payload = p

            if not payload:
                QMessageBox.warning(self, "Erreur", "Aucune donnée Pappers reçue.")
                return

            self.fill_etablissement_from_pappers(payload, payload)
            self.fill_siege_from_pappers(payload)

            QMessageBox.information(self, "Succès", "Champs remplis automatiquement via Pappers.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'appel API : {e}")

    def build_siege_identite_box(self):
        box = QGroupBox("Identité du Siège - Siren - Siret - Tva - Nom")
        grid = QGridLayout()

        self.siege_siren = QLineEdit()
        self.siege_siren.setMaxLength(9)

        self.siege_nic = QLineEdit()
        self.siege_nic.setMaxLength(5)
        self.siege_nic.setInputMask("00000")

        self.siege_siret = QLineEdit()
        self.siege_siret.setReadOnly(True)

        self.siege_tva = QLineEdit()
        self.siege_tva.setReadOnly(True)

        self.siege_nom_entreprise = QLineEdit()

        self.btn_pappers_siege = QPushButton("🔍 Remplir automatiquement (Siège)")

        # Auto SIRET + TVA
        self.siege_siren.textChanged.connect(self.update_siege_siret_tva)
        self.siege_nic.textChanged.connect(self.update_siege_siret_tva)

        # 🔥 Connexion du bouton (OBLIGATOIRE)
        self.btn_pappers_siege.clicked.connect(self.on_pappers_clicked)

        row = 0

        grid.addWidget(QLabel("SIREN siège"), row, 0)
        grid.addWidget(self.siege_siren, row, 1)

        label_siege_nic = QLabel("NIC siège")
        label_siege_nic.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(label_siege_nic, row, 2)
        grid.addWidget(self.siege_nic, row, 3)
        row += 1

        grid.addWidget(QLabel("SIRET siège"), row, 0)
        grid.addWidget(self.siege_siret, row, 1)

        grid.addWidget(QLabel("TVA Intracom siège"), row, 2)
        grid.addWidget(self.siege_tva, row, 3)
        row += 1

        grid.addWidget(QLabel("Nom du siège"), row, 0)
        grid.addWidget(self.siege_nom_entreprise, row, 1, 1, 3)
        row += 1

        grid.addWidget(self.btn_pappers_siege, row, 0, 1, 4, alignment=Qt.AlignCenter)

        box.setLayout(grid)
        return box


    def build_siege_coordonnees_box(self):
        box = QGroupBox("Adresses et Contacts (Siège)")
        grid = QGridLayout()

        label_coord = QLabel("Coordonnées")
        label_coord.setStyleSheet("font-weight: bold; font-size: 15px;")

        label_contact = QLabel("Contacts")
        label_contact.setStyleSheet("font-weight: bold; font-size: 15px;")

        grid.addWidget(label_coord, 0, 0, 1, 2)
        grid.addWidget(label_contact, 0, 2, 1, 2, alignment=Qt.AlignRight)

        # GAUCHE
        self.siege_adresse1 = QLineEdit()
        self.siege_adresse2 = QLineEdit()
        self.siege_complement = QLineEdit()
        self.siege_cp = QLineEdit()
        self.siege_ville = QLineEdit()

        self.siege_region = QComboBox()
        self.siege_region.addItems([r for r in [*DEPARTEMENT_TO_REGION.values()]])

        self.siege_pays = QComboBox()
        self.siege_pays.addItems(["France", "Belgique", "Suisse", "Luxembourg"])

        # DROITE
        self.siege_tel_fixe = QLineEdit()
        self.siege_tel_port = QLineEdit()
        self.siege_email = QLineEdit()
        self.siege_web = QLineEdit()
        self.siege_resp_nom = QLineEdit()
        self.siege_resp_tel = QLineEdit()
        self.siege_resp_email = QLineEdit()

        row = 1

        grid.addWidget(QLabel("Adresse (ligne 1)"), row, 0)
        grid.addWidget(self.siege_adresse1, row, 1)
        grid.addWidget(QLabel("📞 Téléphone fixe"), row, 2)
        grid.addWidget(self.siege_tel_fixe, row, 3)
        row += 1

        grid.addWidget(QLabel("Adresse (ligne 2)"), row, 0)
        grid.addWidget(self.siege_adresse2, row, 1)
        grid.addWidget(QLabel("📱 Portable"), row, 2)
        grid.addWidget(self.siege_tel_port, row, 3)
        row += 1

        grid.addWidget(QLabel("Complément"), row, 0)
        grid.addWidget(self.siege_complement, row, 1)
        grid.addWidget(QLabel("✉️ Email"), row, 2)
        grid.addWidget(self.siege_email, row, 3)
        row += 1

        grid.addWidget(QLabel("Code postal"), row, 0)
        grid.addWidget(self.siege_cp, row, 1)
        grid.addWidget(QLabel("🌐 Site web"), row, 2)
        grid.addWidget(self.siege_web, row, 3)
        row += 1

        grid.addWidget(QLabel("Ville"), row, 0)
        grid.addWidget(self.siege_ville, row, 1)
        grid.addWidget(QLabel("👤 Responsable"), row, 2)
        grid.addWidget(self.siege_resp_nom, row, 3)
        row += 1

        grid.addWidget(QLabel("Région"), row, 0)
        grid.addWidget(self.siege_region, row, 1)
        grid.addWidget(QLabel("📞 Téléphone Resp."), row, 2)
        grid.addWidget(self.siege_resp_tel, row, 3)
        row += 1

        grid.addWidget(QLabel("Pays"), row, 0)
        grid.addWidget(self.siege_pays, row, 1)
        grid.addWidget(QLabel("✉️ Email Resp."), row, 2)
        grid.addWidget(self.siege_resp_email, row, 3)

        box.setLayout(grid)
        return box

    def build_siege_juridique_box(self):
        box = QGroupBox("Informations juridiques — Siège")
        grid = QGridLayout()

        # Ligne 1
        grid.addWidget(self.siege_label_forme,          0, 0)
        grid.addWidget(self.siege_forme,                0, 1)
        grid.addWidget(self.siege_label_nom_commercial, 0, 2)
        grid.addWidget(self.siege_nom_commercial,       0, 3)

        # Ligne 2
        grid.addWidget(self.siege_label_frp,            1, 0)
        grid.addWidget(self.siege_frp,                  1, 1)
        grid.addWidget(self.siege_label_cdi,            1, 2)
        grid.addWidget(self.siege_cdi,                  1, 3)

        # Ligne 3
        grid.addWidget(self.siege_label_service,        2, 0)
        grid.addWidget(self.siege_service,              2, 1)
        grid.addWidget(self.siege_label_rc,             2, 2)
        grid.addWidget(self.siege_rc,                   2, 3)

        # Ligne 4
        grid.addWidget(self.siege_label_naf,            3, 0)
        grid.addWidget(self.siege_naf,                  3, 1)
        grid.addWidget(self.siege_label_naf_def,        3, 2)
        grid.addWidget(self.siege_naf_def,              3, 3)

        # Ligne 5
        grid.addWidget(self.siege_label_capital,        4, 0)
        grid.addWidget(self.siege_capital,              4, 1)
        grid.addWidget(self.siege_label_parts,          4, 2)
        grid.addWidget(self.siege_parts,                4, 3)

        # Ligne 6
        grid.addWidget(self.siege_label_date_creation,  5, 0)
        grid.addWidget(self.siege_date_creation,        5, 1)
        grid.addWidget(self.siege_label_date_cloture,   5, 2)
        grid.addWidget(self.siege_date_cloture,         5, 3)

        box.setLayout(grid)
        return box

    def build_siege_fiscalite_box(self):
        box = QGroupBox("Régime Fiscal & TVA (Siège)")
        grid = QGridLayout()

        self.siege_type_dossier = QComboBox()
        self.siege_type_dossier.addItems(["BIC", "BNC", "BA"])

        self.siege_regime_fiscal = QComboBox()
        self.siege_regime_fiscal.addItems(["Réel simplifié", "Réel normal", "Micro"])

        self.siege_imposition = QComboBox()
        self.siege_imposition.addItems(["IS", "IR"])

        self.siege_regime_tva = QComboBox()
        self.siege_regime_tva.addItems(["Réel simplifié", "Réel normal", "Franchise en base"])

        self.siege_tva2 = QLineEdit()
        self.siege_tva2.setReadOnly(True)

        grid.addWidget(QLabel("Type de dossier"), 0, 0)
        grid.addWidget(self.siege_type_dossier, 0, 1)

        grid.addWidget(QLabel("Régime fiscal"), 1, 0)
        grid.addWidget(self.siege_regime_fiscal, 1, 1)

        grid.addWidget(QLabel("Imposition"), 2, 0)
        grid.addWidget(self.siege_imposition, 2, 1)

        grid.addWidget(QLabel("Régime TVA"), 3, 0)
        grid.addWidget(self.siege_regime_tva, 3, 1)

        grid.addWidget(QLabel("TVA Intracom"), 4, 0)
        grid.addWidget(self.siege_tva2, 4, 1)

        box.setLayout(grid)
        return box

    # ---------------------------------------------------------
    # MARQUAGE VISUEL DES CHAMPS AUTO‑REMPLIS
    # ---------------------------------------------------------
    def mark_autofilled(self, widget):
        widget.setStyleSheet("background-color: #E8F5FF;")

    def _combo_value(self, combo):
        value = combo.currentText().strip()
        return value or None

    def _set_combo_text(self, combo, value):
        value = value or ""
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
        elif value:
            combo.addItem(value)
            combo.setCurrentText(value)

    def _api_error_message(self, response):
        try:
            payload = response.json()
        except ValueError:
            return response.text

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if detail:
                return str(detail)
        return response.text

    # ---------------------------------------------------------
    # SAUVEGARDE
    # ---------------------------------------------------------
    def save_dossier(self):
        """Enregistre ou modifie un dossier selon le mode."""
        if not self.validate_required():
            QMessageBox.warning(
                self,
                "Champs obligatoires",
                "Renseignez au minimum le nom de l'entreprise. Le SIREN doit contenir 9 chiffres s'il est saisi.",
            )
            return None

        self.update_siret_tva()
        data = {
            "siren": self.siren.text(),
            "nic": self.nic.text(),
            "siret": self.siret.text(),
            "tva_intracom": self.tva.text(),
            "nom_entreprise": self.nom_entreprise.text(),
            "adresse1": self.adresse1.text(),
            "adresse2": self.adresse2.text(),
            "complement": self.complement.text(),
            "cp": self.cp.text(),
            "ville": self.ville.text(),
            "region": self._combo_value(self.region),
            "pays": self._combo_value(self.pays),
            "email": self.email.text(),
            "web": self.web.text(),
            "tel_fixe": self.tel_fixe.text(),
            "tel_port": self.tel_port.text(),
            "resp_nom": self.resp_nom.text(),
            "resp_tel": self.resp_tel.text(),
            "resp_email": self.resp_email.text(),
            "forme": self._combo_value(self.forme),
            "nom_commercial": self.nom_commercial.text(),
            "frp": self._combo_value(self.frp),
            "cdi": self._combo_value(self.cdi),
            "service": self._combo_value(self.service),
            "rc": self.rc.text(),
            "naf": self.naf.text(),
            "naf_def": self.naf_def.text(),
            "capital": self.capital.text(),
            "parts": self.parts.text(),
            "date_creation": self.date_creation.text(),
            "date_cloture": self.date_cloture.text(),
            "type_dossier": self._combo_value(self.type_dossier),
            "regime_fiscal": self._combo_value(self.regime_fiscal),
            "imposition": self._combo_value(self.imposition),
            "regime_tva": self._combo_value(self.regime_tva),
        }

        try:
            if self.dossier_id is None:
                # CRÉATION
                url = api_url("/dossiers/")
                r = requests.post(url, json=data, timeout=10)
            else:
                # MODIFICATION
                url = api_url(f"/dossiers/{self.dossier_id}")
                r = requests.put(url, json=data, timeout=10)

            if not r.ok:
                raise RuntimeError(self._api_error_message(r))

            saved = r.json()
            self.dossier_id = saved.get("id", self.dossier_id)
            return saved

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible d’enregistrer : {e}")
            return None


    def load_dossier_for_edit(self):
        """Charge les données du dossier depuis l’API et remplit les champs."""
        try:
            url = api_url(f"/dossiers/{self.dossier_id}")
            r = requests.get(url)
            r.raise_for_status()
            d = r.json()

            # IDENTITÉ
            self.siren.setText(d.get("siren", ""))
            self.nic.setText(d.get("nic", ""))
            self.nom_entreprise.setText(d.get("nom_entreprise", ""))
            self.tva.setText(d.get("tva_intracom", ""))
            self.tva2.setText(d.get("tva_intracom", ""))

            # COORDONNÉES
            self.adresse1.setText(d.get("adresse1", ""))
            self.adresse2.setText(d.get("adresse2", ""))
            self.complement.setText(d.get("complement", ""))
            self.cp.setText(d.get("cp", ""))
            self.ville.setText(d.get("ville", ""))
            self._set_combo_text(self.region, d.get("region"))
            self._set_combo_text(self.pays, d.get("pays"))
            self.email.setText(d.get("email", ""))
            self.web.setText(d.get("web", ""))
            self.tel_fixe.setText(d.get("tel_fixe", ""))
            self.tel_port.setText(d.get("tel_port", ""))
            self.resp_nom.setText(d.get("resp_nom", ""))
            self.resp_tel.setText(d.get("resp_tel", ""))
            self.resp_email.setText(d.get("resp_email", ""))

            # JURIDIQUE
            self._set_combo_text(self.forme, d.get("forme"))
            self.nom_commercial.setText(d.get("nom_commercial", ""))
            self._set_combo_text(self.frp, d.get("frp"))
            self._set_combo_text(self.cdi, d.get("cdi"))
            self._set_combo_text(self.service, d.get("service"))
            self.rc.setText(d.get("rc", ""))
            self.naf.setText(d.get("naf", ""))
            self.naf_def.setText(d.get("naf_def", ""))
            self.capital.setText(d.get("capital", ""))
            self.parts.setText(d.get("parts", ""))
            self.date_creation.setText(d.get("date_creation", ""))
            self.date_cloture.setText(d.get("date_cloture", ""))

            # FISCALITÉ
            self._set_combo_text(self.type_dossier, d.get("type_dossier"))
            self._set_combo_text(self.regime_fiscal, d.get("regime_fiscal"))
            self._set_combo_text(self.imposition, d.get("imposition"))
            self._set_combo_text(self.regime_tva, d.get("regime_tva"))

            # Recalcul auto
            self.update_siret_tva()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le dossier : {e}")

    def on_save_clicked(self):
        saved = self.save_dossier()
        if saved:
            QMessageBox.information(self, "Succès", "Dossier enregistré.")

    def on_save_quit_clicked(self):
        saved = self.save_dossier()
        if saved:
            QMessageBox.information(self, "Succès", "Dossier enregistré.")
            self.accept()   # ferme la fenêtre et renvoie QDialog.Accepted

    def on_cancel_clicked(self):
        self.close()

    # ---------------------------------------------------------
    # FERMETURE AVEC CONFIRMATION
    # ---------------------------------------------------------
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Annuler",
            "Les modifications ne seront pas enregistrées.\n\n"
            "Voulez-vous vraiment fermer la fenêtre ?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # ---------------------------------------------------------
    # CENTRAGE
    # ---------------------------------------------------------
    def center_on_screen(self):
        screen = self.screen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
