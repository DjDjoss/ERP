import sqlite3
import os

DB_NAME = "erp.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    """Crée toutes les tables si elles n'existent pas."""
    conn = get_connection()
    cur = conn.cursor()

    # TABLE DOSSIERS
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dossiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            annee TEXT NOT NULL,
            secteur TEXT,
            date_creation TEXT
        )
    """)

    # TABLE JOURNAUX
    cur.execute("""
        CREATE TABLE IF NOT EXISTS journaux (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id INTEGER NOT NULL,
            code TEXT NOT NULL,
            libelle TEXT NOT NULL,
            ordre INTEGER,
            FOREIGN KEY(dossier_id) REFERENCES dossiers(id)
        )
    """)

    # TABLE PCG (plan comptable général importé)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pcg (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id INTEGER NOT NULL,
            numero TEXT NOT NULL,
            intitule TEXT NOT NULL,
            type TEXT,
            FOREIGN KEY(dossier_id) REFERENCES dossiers(id)
        )
    """)

    # TABLE COMPTES (si tu veux un PCG sectoriel)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS comptes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id INTEGER NOT NULL,
            secteur TEXT,
            compte TEXT NOT NULL,
            intitule TEXT NOT NULL,
            type TEXT,
            longueur INTEGER,
            FOREIGN KEY(dossier_id) REFERENCES dossiers(id)
        )
    """)

    # TABLE ECRITURES (pour plus tard)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ecritures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dossier_id INTEGER NOT NULL,
            journal_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            compte TEXT NOT NULL,
            libelle TEXT,
            debit REAL,
            credit REAL,
            FOREIGN KEY(dossier_id) REFERENCES dossiers(id),
            FOREIGN KEY(journal_id) REFERENCES journaux(id)
        )
    """)

    conn.commit()
    conn.close()


# Initialisation automatique au lancement
if not os.path.exists(DB_NAME):
    init_db()
else:
    # On vérifie quand même que les tables existent
    init_db()
