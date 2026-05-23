# -*- coding: utf-8 -*-
"""
Configuration de la base de données - PostgreSQL uniquement

Ce module centralise toute la configuration PostgreSQL pour le projet.
Conformément aux exigences, SQLite n'est PAS supporté.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from sqlalchemy.pool import QueuePool

# =============================================================================
# CONFIGURATION POSTGRESQL - OBLIGATOIRE
# =============================================================================

# Variables d'environnement requises
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME_MASTER = os.getenv("DB_NAME_MASTER", "erp_djoss")

# Construction de l'URL de connexion
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME_MASTER}"

# Configuration du pool de connexions
engine_master = create_engine(
    DATABASE_URL,
    echo=False,  # Mettre à True pour le débogage SQL
    client_encoding="utf8",
    poolclass=QueuePool,
    pool_size=15,
    max_overflow=25,
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    pool_recycle=3600,   # Recycle les connexions après 1 heure
    connect_args={
        "options": "-c timezone=UTC"  # Force UTC comme timezone
    }
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_master,
    expire_on_commit=False
)

# Session thread-safe pour les opérations concurrentes
ScopedSession = scoped_session(SessionLocal)

# Base déclarative pour les modèles SQLAlchemy
Base = declarative_base()


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def init_master_db() -> None:
    """
    Initialise la base de données maître en créant toutes les tables.
    Doit être appelé au démarrage de l'application.
    """
    from finance.models import Base as FinanceBase
    from dossiers.models import Base as DossiersBase
    
    # Crée toutes les tables définies dans les modèles
    Base.metadata.create_all(bind=engine_master)
    print("[OK] Base de données maître initialisée")


def get_db():
    """
    Générateur de session pour FastAPI (dependency injection).
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = ScopedSession()
    try:
        yield db
    finally:
        db.close()


def get_master_db():
    """
    Retourne une session directe vers la base maître.
    À utiliser en dehors du contexte FastAPI.
    """
    return SessionLocal()


def create_dossier_database(db_name: str) -> bool:
    """
    Crée une nouvelle base de données pour un dossier client.
    
    Args:
        db_name: Nom de la base de données à créer
        
    Returns:
        bool: True si la création a réussi, False sinon
        
    Raises:
        Exception: Si la base existe déjà ou erreur de création
    """
    from sqlalchemy import text
    
    # Connexion à la base postgres par défaut pour créer la nouvelle base
    admin_engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    try:
        with admin_engine.connect() as conn:
            # Vérifie si la base existe déjà
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            ).first()
            
            if result:
                print(f"[INFO] La base {db_name} existe déjà")
                return False
            
            # Crée la base avec encodage français
            conn.execute(
                text(f"""
                    CREATE DATABASE "{db_name}" 
                    WITH ENCODING 'UTF8' 
                    LC_COLLATE='fr_FR.UTF-8' 
                    LC_CTYPE='fr_FR.UTF-8' 
                    TEMPLATE=template0
                """)
            )
            print(f"[OK] Base dossier créée : {db_name}")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Échec création base {db_name}: {str(e)}")
        raise
    finally:
        admin_engine.dispose()


def drop_dossier_database(db_name: str) -> bool:
    """
    Supprime une base de données dossier.
    
    Args:
        db_name: Nom de la base de données à supprimer
        
    Returns:
        bool: True si la suppression a réussi
    """
    from sqlalchemy import text
    
    admin_engine = create_engine(
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    try:
        with admin_engine.connect() as conn:
            # Ferme toutes les connexions actives vers cette base
            conn.execute(
                text(f"""
                    SELECT pg_terminate_backend(pid) 
                    FROM pg_stat_activity 
                    WHERE datname = :db_name AND pid <> pg_backend_pid()
                """),
                {"db_name": db_name}
            )
            
            # Supprime la base
            conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
            print(f"[OK] Base dossier supprimée : {db_name}")
            return True
            
    except Exception as e:
        print(f"[ERREUR] Échec suppression base {db_name}: {str(e)}")
        raise
    finally:
        admin_engine.dispose()


def get_dossier_engine(db_name: str):
    """
    Retourne un engine SQLAlchemy pour une base dossier spécifique.
    
    Args:
        db_name: Nom de la base du dossier
        
    Returns:
        Engine: Moteur SQLAlchemy configuré
    """
    dossier_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    
    return create_engine(
        dossier_url,
        echo=False,
        client_encoding="utf8",
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=15,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


def get_dossier_session(db_name: str):
    """
    Crée une session ORM pour une base dossier spécifique.
    
    Args:
        db_name: Nom de la base du dossier
        
    Returns:
        Session: Session SQLAlchemy
    """
    engine = get_dossier_engine(db_name)
    DossierSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
    return DossierSessionLocal()


def check_postgresql_connection() -> bool:
    """
    Vérifie que la connexion PostgreSQL est opérationnelle.
    
    Returns:
        bool: True si la connexion fonctionne
    """
    try:
        connection = engine_master.connect()
        connection.close()
        return True
    except Exception as e:
        print(f"[ERREUR] Connexion PostgreSQL échouée: {str(e)}")
        return False


# =============================================================================
# INITIALISATION AUTOMATIQUE AU CHARGEMENT DU MODULE
# =============================================================================

if __name__ == "__main__":
    # Test de connexion lors de l'exécution directe
    if check_postgresql_connection():
        print("✅ Connexion PostgreSQL OK")
    else:
        print("❌ Échec connexion PostgreSQL")
        exit(1)
