from logging.config import fileConfig
import sys
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ------------------------------------------------------------
# CONFIG ALEMBIC
# ------------------------------------------------------------

config = context.config

# Logging Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------
# IMPORTS DE TON PROJET
# ------------------------------------------------------------
# On ajoute la racine du projet au PYTHONPATH
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# Import du Base SQLAlchemy et des modèles
from backend.connection_manager import Base
from backend.modules.dossiers import models  # IMPORTANT : permet à Alembic de voir la table Dossier

# C’est la metadata que Alembic utilise pour comparer modèle ↔ base
target_metadata = Base.metadata


# ------------------------------------------------------------
# MODE OFFLINE
# ------------------------------------------------------------
def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline'."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------
# MODE ONLINE
# ------------------------------------------------------------
def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,      # compare les types SQL
            compare_server_default=True,  # compare les valeurs par défaut
        )

        with context.begin_transaction():
            context.run_migrations()


# ------------------------------------------------------------
# POINT D’ENTRÉE ALEMBIC
# ------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
