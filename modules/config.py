import os


API_BASE_URL = os.getenv("ERP_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def api_url(path: str) -> str:
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{API_BASE_URL}{normalized}"

