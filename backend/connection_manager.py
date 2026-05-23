import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from backend.settings import settings

# ---------------------------------------------------------
# CONFIGURATION PRINCIPALE
# ---------------------------------------------------------

DB_USER = settings.db_user
DB_PASSWORD = settings.db_password
DB_HOST = settings.db_host
DB_PORT = str(settings.db_port)
DB_NAME_MASTER = settings.db_name_master

DATABASE_URL_MASTER = settings.database_url_master
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Create engine_master safely: handle missing URL or SQLite URLs (no postgres-only kwargs)
if not DATABASE_URL_MASTER:
    # Fallback local persistant pour permettre un ERP utilisable sans PostgreSQL.
    DATABASE_URL_MASTER = f"sqlite+pysqlite:///{PROJECT_ROOT / 'erp_backend.db'}"
    engine_master = create_engine(
        DATABASE_URL_MASTER,
        echo=False,
        connect_args={"check_same_thread": False},
    )
else:
    # If SQLite URL, avoid postgres-only kwargs like client_encoding
    if DATABASE_URL_MASTER.startswith("sqlite"):
        engine_master = create_engine(
            DATABASE_URL_MASTER,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    else:
        engine_master = create_engine(
            DATABASE_URL_MASTER,
            echo=False,
            client_encoding="utf8"
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_master)

Base = declarative_base()


def init_master_db() -> None:
    Base.metadata.create_all(bind=engine_master)

# ---------------------------------------------------------
# SESSION POUR FASTAPI (BASE MAÎTRE)
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------------------------------------
# 1) SESSION SUR LA BASE MAÎTRE
# ---------------------------------------------------------

def get_master_db():
    """Retourne une session ORM vers la base maître ERP_Rosan."""
    return SessionLocal()


# ---------------------------------------------------------
# 2) CRÉATION D’UNE BASE DOSSIER
# ---------------------------------------------------------

def create_dossier_database(db_name: str):
    engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT"
    )
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(f'CREATE DATABASE "{db_name}" ENCODING \'UTF8\';'))
        print(f"[OK] Base dossier créée : {db_name}")


# ---------------------------------------------------------
# 3) ENGINE SUR UNE BASE DOSSIER
# ---------------------------------------------------------

def get_dossier_engine(db_name: str):
    return create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}",
        echo=False,
        client_encoding="utf8"
    )


# ---------------------------------------------------------
# 4) SESSION ORM SUR UNE BASE DOSSIER
# ---------------------------------------------------------

def get_dossier_session(db_name: str):
    engine = get_dossier_engine(db_name)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)()
