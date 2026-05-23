import os
from pathlib import Path


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env.local"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_text_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value.strip().strip('"').strip("'")
    return default


class Settings:
    # PostgreSQL (backend API)
    db_user: str = os.getenv("DB_USER", "ERP_Rosan")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = _get_int_env("DB_PORT", 5432)
    db_name_master: str = os.getenv("DB_NAME_MASTER", "ERP_Rosan")
    database_url_master: str = os.getenv("DATABASE_URL_MASTER", "")

    # Pappers
    pappers_api_key: str = _get_text_env("PAPPERS_API_KEY")
    pappers_base_url: str = _get_text_env(
        "PAPPERS_BASE_URL",
        "PAPPERS_URL",
        default="https://api.pappers.fr/v2/entreprise",
    )
    pappers_timeout_seconds: float = _get_float_env("PAPPERS_TIMEOUT_SECONDS", 10.0)
    pappers_mock_mode: bool = _get_bool_env("PAPPERS_MOCK_MODE", False)

    # INSEE
    insee_token_url: str = os.getenv("INSEE_TOKEN_URL", "https://api.insee.fr/token").strip()
    insee_api_url: str = os.getenv(
        "INSEE_API_URL", "https://api.insee.fr/entreprises/sirene/V3/siret/"
    ).strip()
    insee_client_id: str = os.getenv("INSEE_CLIENT_ID", "").strip()
    insee_client_secret: str = os.getenv("INSEE_CLIENT_SECRET", "").strip()

    # Orchestrateur
    postgres_service: str = os.getenv("POSTGRES_SERVICE", "postgresql-x64-18")
    postgres_port: int = _get_int_env("POSTGRES_PORT", 5432)
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_db: str = os.getenv("POSTGRES_DB", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")

    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = _get_int_env("BACKEND_PORT", 8000)
    orchestrator_aggressive_cleanup: bool = _get_bool_env(
        "ORCHESTRATOR_AGGRESSIVE_CLEANUP", False
    )
    orchestrator_allow_kill_port_5432: bool = _get_bool_env(
        "ORCHESTRATOR_ALLOW_KILL_PORT_5432", False
    )


settings = Settings()
