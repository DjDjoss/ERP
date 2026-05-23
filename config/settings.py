import os
from typing import Optional

# Centralise l'accès aux variables d'environnement utilisées par le projet.
# Lire directement depuis os.environ pour éviter d'avoir des secrets en dur.

def get_env(name: str, default: Optional[str]=None) -> Optional[str]:
    return os.environ.get(name, default)

# Pappers
PAPPERS_API_KEY = get_env("PAPPERS_API_KEY")
PAPPERS_BASE_URL = get_env("PAPPERS_BASE_URL", "https://api.pappers.fr/v1")
PAPPERS_TIMEOUT_SECONDS = float(get_env("PAPPERS_TIMEOUT_SECONDS", 10))

# Database
DB_HOST = get_env("DB_HOST", "localhost")
DB_PORT = int(get_env("DB_PORT", 5432)) if get_env("DB_PORT") else 5432
DB_NAME = get_env("DB_NAME", "erp_db")
DB_USER = get_env("DB_USER", "erp_user")
DB_PASSWORD = get_env("DB_PASSWORD")

# Redis
REDIS_URL = get_env("REDIS_URL")

# Other
SENTRY_DSN = get_env("SENTRY_DSN")
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")
