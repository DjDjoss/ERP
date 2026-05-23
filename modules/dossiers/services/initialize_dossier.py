from sqlalchemy import text
from modules.dossiers.services.connection_manager import get_dossier_engine
from datetime import date


# ---------------------------------------------------------
# 1) Création du schéma SQL
# ---------------------------------------------------------
def initialize_schema(db_name: str):
    """
    Applique le schéma SQL de base dans la base du dossier.
    Tables essentielles : comptes, journaux, exercices.
    """

    engine = get_dossier_engine(db_name)

    schema_sql = """
    CREATE TABLE IF NOT EXISTS accounts (
        id SERIAL PRIMARY KEY,
        code VARCHAR(20) NOT NULL,
        label VARCHAR(255) NOT NULL,
        type VARCHAR(20) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS journals (
        id SERIAL PRIMARY KEY,
        code VARCHAR(10) NOT NULL,
        label VARCHAR(255) NOT NULL,
        type VARCHAR(20) NOT NULL
    );

    CREATE TABLE IF NOT EXISTS fiscal_years (
        id SERIAL PRIMARY KEY,
        code VARCHAR(10) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status VARCHAR(10) NOT NULL
    );
    """

    with engine.connect() as conn:
        conn.execute(text(schema_sql))
        conn.commit()


# ---------------------------------------------------------
# 2) Journaux comptables standards
# ---------------------------------------------------------
def initialize_journals(db_name: str):
    """
    Crée les journaux comptables standards.
    Si un journal existe déjà, il n'est pas recréé.
    """

    engine = get_dossier_engine(db_name)

    journals = [
        ("ACHA", "Achats", "PURCHASE"),
        ("VENT", "Ventes", "SALE"),
        ("BNK", "Banque", "BANK"),
        ("CAIS", "Caisse", "CASH"),
        ("OD", "Opérations diverses", "GENERAL"),
    ]

    with engine.connect() as conn:
        for code, label, jtype in journals:
            conn.execute(
                text("""
                    INSERT INTO journals (code, label, type)
                    SELECT :code, :label, :type
                    WHERE NOT EXISTS (
                        SELECT 1 FROM journals WHERE code = :code
                    )
                """),
                {"code": code, "label": label, "type": jtype}
            )
        conn.commit()


# ---------------------------------------------------------
# 3) PCG minimal
# ---------------------------------------------------------
def initialize_pcg_minimal(db_name: str):
    """
    Insère un PCG minimal.
    Aucun doublon possible.
    """

    engine = get_dossier_engine(db_name)

    accounts = [
        ("401", "Fournisseurs", "LIABILITY"),
        ("411", "Clients", "ASSET"),
        ("512", "Banque", "ASSET"),
        ("606", "Achats non stockés", "EXPENSE"),
        ("44566", "TVA déductible", "ASSET"),
        ("44571", "TVA collectée", "LIABILITY"),
        ("707", "Ventes de marchandises", "INCOME"),
    ]

    with engine.connect() as conn:
        for code, label, atype in accounts:
            conn.execute(
                text("""
                    INSERT INTO accounts (code, label, type)
                    SELECT :code, :label, :type
                    WHERE NOT EXISTS (
                        SELECT 1 FROM accounts WHERE code = :code
                    )
                """),
                {"code": code, "label": label, "type": atype}
            )
        conn.commit()


# ---------------------------------------------------------
# 4) Exercice comptable
# ---------------------------------------------------------
def initialize_fiscal_year(db_name: str):
    """
    Crée l’exercice comptable en cours.
    Un seul exercice par année.
    """

    engine = get_dossier_engine(db_name)

    year = date.today().year
    start = date(year, 1, 1)
    end = date(year, 12, 31)

    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO fiscal_years (code, start_date, end_date, status)
                SELECT :code, :start, :end, 'OPEN'
                WHERE NOT EXISTS (
                    SELECT 1 FROM fiscal_years WHERE code = :code
                )
            """),
            {"code": str(year), "start": start, "end": end}
        )
        conn.commit()


# ---------------------------------------------------------
# 5) Initialisation complète du dossier
# ---------------------------------------------------------
def initialize_dossier(db_name: str):
    """
    Fonction principale : initialise complètement un dossier.
    Appelée juste après la création de la base PostgreSQL.
    """

    print(f"→ Initialisation du dossier : {db_name}")

    initialize_schema(db_name)
    print("  ✓ Schéma SQL appliqué")

    initialize_journals(db_name)
    print("  ✓ Journaux standards créés")

    initialize_pcg_minimal(db_name)
    print("  ✓ PCG minimal inséré")

    initialize_fiscal_year(db_name)
    print("  ✓ Exercice comptable créé")

    print(f"✓ Dossier {db_name} initialisé avec succès")
