import subprocess
import time
import sys
import os

POSTGRES_SERVICE = "postgresql-x64-18"


# ---------------------------------------------------------
# 1) Lire l'état EXACT du service PostgreSQL
# ---------------------------------------------------------
def get_postgres_service_state():
    result = subprocess.run(
        ["sc", "query", POSTGRES_SERVICE],
        capture_output=True,
        text=True,
        shell=True
    )
    output = result.stdout.upper()

    if "STATE" not in output:
        return "UNKNOWN"

    for line in output.splitlines():
        if "STATE" in line:
            parts = line.split()
            return parts[-1]  # RUNNING, STOPPED, etc.

    return "UNKNOWN"


def is_postgres_service_running():
    return get_postgres_service_state() == "RUNNING"


# ---------------------------------------------------------
# 2) Démarrer PostgreSQL
# ---------------------------------------------------------
def start_postgres_service():
    print(f"🔄 PostgreSQL n'est pas actif. Démarrage du service : {POSTGRES_SERVICE}")

    subprocess.run(
        ["net", "start", POSTGRES_SERVICE],
        capture_output=True,
        text=True,
        shell=True
    )

    print("⏳ Attente du démarrage de PostgreSQL...")

    for _ in range(30):
        if is_postgres_service_running():
            print("✅ PostgreSQL est opérationnel.")
            return True
        time.sleep(0.5)

    print("❌ PostgreSQL ne démarre pas.")
    return False


# ---------------------------------------------------------
# 3) Lancer Uvicorn (VISIBLE dans la console)
# ---------------------------------------------------------
def start_uvicorn():
    print("🚀 Lancement du backend uvicorn...")

    # IMPORTANT :
    # stdout=None et stderr=None => Uvicorn affiche dans la console actuelle
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload", "--port", "8000"],
        stdout=None,
        stderr=None,
        shell=False
    )


# ---------------------------------------------------------
# 4) Fonction principale
# ---------------------------------------------------------
def ensure_backend_running():
    print("🔍 Vérification du statut PostgreSQL...")

    state = get_postgres_service_state()
    print(f"   → État actuel du service PostgreSQL : {state}")

    if state != "RUNNING":
        if not start_postgres_service():
            print("❌ Impossible de démarrer PostgreSQL. Arrêt.")
            sys.exit(1)

    print("🔍 PostgreSQL est actif.")
    print("🔍 Vérification du backend uvicorn...")

    uvicorn_process = start_uvicorn()

    time.sleep(2)

    print("✅ Backend opérationnel.")
    return uvicorn_process
