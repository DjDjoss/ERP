import psycopg2
from psycopg2 import sql
from psycopg2.extensions import register_type, UNICODE
from backend.settings import settings

# Force psycopg2 to always return Unicode-safe strings
register_type(UNICODE)

POSTGRES_MASTER_CONFIG = {
    "user": settings.db_user,
    "password": settings.db_password,
    "host": settings.db_host,
    "port": settings.db_port,
}


def _sanitize_pg_error(e: Exception) -> str:
    """
    Nettoie une erreur PostgreSQL pour la rendre 100% ASCII.
    Compatible Windows CP1252.
    Empêche les crashs 'utf-8 codec can't decode byte 0x..'
    """
    if hasattr(e, "diag") and e.diag is not None:
        msg = e.diag.message_primary or ""
    elif hasattr(e, "pgerror") and e.pgerror:
        msg = e.pgerror
    else:
        msg = str(e)

    # Convertit en ASCII propre
    return msg.encode("ascii", errors="ignore").decode("ascii")


def create_dossier_database(db_name: str):
    """
    Crée une base PostgreSQL pour un dossier.
    Version PRO : définit le propriétaire, corrige le schéma public,
    évite l'erreur InsufficientPrivilege et les erreurs d'encodage Windows.
    """

    if not db_name or not isinstance(db_name, str):
        raise ValueError("Nom de base invalide.")

    if not db_name.startswith("erp_"):
        raise ValueError("Le nom de base doit commencer par 'erp_'")

    conn = None
    try:
        # Connexion à la base postgres pour créer la nouvelle base
        conn = psycopg2.connect(
            dbname="postgres",
            user=POSTGRES_MASTER_CONFIG["user"],
            password=POSTGRES_MASTER_CONFIG["password"],
            host=POSTGRES_MASTER_CONFIG["host"],
            port=POSTGRES_MASTER_CONFIG["port"],
        )
        register_type(UNICODE, conn)  # Sécurise l'encodage
        conn.autocommit = True
        cur = conn.cursor()

        # Vérifier si la base existe déjà
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s;",
            (db_name,)
        )
        exists = cur.fetchone()

        if exists:
            cur.close()
            return {
                "success": False,
                "message": "La base existe deja.",
                "database": db_name
            }

        # Création de la base AVEC propriétaire ERP_Rosan
        cur.execute(
            sql.SQL("CREATE DATABASE {} OWNER {};").format(
                sql.Identifier(db_name),
                sql.Identifier(POSTGRES_MASTER_CONFIG["user"])
            )
        )

        cur.close()
        conn.close()

        # Connexion à la nouvelle base pour corriger le schéma public
        conn2 = psycopg2.connect(
            dbname=db_name,
            user=POSTGRES_MASTER_CONFIG["user"],
            password=POSTGRES_MASTER_CONFIG["password"],
            host=POSTGRES_MASTER_CONFIG["host"],
            port=POSTGRES_MASTER_CONFIG["port"],
        )
        register_type(UNICODE, conn2)  # Sécurise l'encodage
        conn2.autocommit = True
        cur2 = conn2.cursor()

        # Donner la propriété du schéma public à ERP_Rosan
        cur2.execute(
            sql.SQL("ALTER SCHEMA public OWNER TO {};").format(
                sql.Identifier(POSTGRES_MASTER_CONFIG["user"])
            )
        )

        cur2.close()
        conn2.close()

        return {
            "success": True,
            "message": "Base creee avec succes.",
            "database": db_name
        }
    except Exception as e:
        safe = _sanitize_pg_error(e)
        print("### ERREUR POSTGRESQL REELLE ###")
        print(safe)
        raise RuntimeError(f"Erreur creation base {db_name}: {safe}")


    finally:
        if conn is not None:
            conn.close()
