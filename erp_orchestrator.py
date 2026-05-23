# erp_orchestrator.py
# -*- coding: utf-8 -*-

import sys
import os
import subprocess
import time
import socket
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import getpass


PROJECT_ROOT = Path(__file__).resolve().parent


def load_local_env(env_path: Path | None = None) -> None:
    """Charge .env.local sans ecraser les variables deja definies."""
    env_path = env_path or PROJECT_ROOT / ".env.local"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()

from backend.settings import settings

# =========================
# CONFIG
# =========================

POSTGRES_SERVICE = settings.postgres_service
POSTGRES_PORT = settings.postgres_port
POSTGRES_USER = settings.postgres_user
POSTGRES_DB = settings.postgres_db
POSTGRES_PASSWORD = settings.postgres_password

BACKEND_HOST = settings.backend_host
BACKEND_PORT = settings.backend_port

LOG_FILE = "erp_launcher.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

LOCKFILE_PATH = PROJECT_ROOT / "erp_launcher.lock"


def uses_postgres_master_db() -> bool:
    url = settings.database_url_master.strip().lower()
    return url.startswith("postgresql://") or url.startswith("postgresql+")

# =========================
# LOGGING
# =========================

class MemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(self.format(record))


memory_handler = MemoryLogHandler()


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("erp_launcher")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    memory_handler.setFormatter(fmt)
    logger.addHandler(memory_handler)

    return logger


log = setup_logger()

# =========================
# OUTILS SYSTÈME
# =========================

def run(cmd: str, timeout: int = 10):
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
        )
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out.strip(), err.strip()
    except Exception as e:
        return -1, "", str(e)


def python_has_module(python_exe: Path, module_name: str) -> bool:
    if not python_exe.exists():
        return False
    code, _, _ = run(f'"{python_exe}" -c "import {module_name}"', timeout=5)
    return code == 0


def python_has_modules(python_exe: Path, module_names: list[str]) -> bool:
    if not python_exe.exists():
        return False
    imports = "; ".join(f"import {module}" for module in module_names)
    code, _, _ = run(f'"{python_exe}" -c "{imports}"', timeout=8)
    return code == 0


def repair_project_env() -> bool:
    venv_dir = PROJECT_ROOT / ".venv"
    venv_python = venv_dir / "Scripts" / "python.exe"
    requirements = PROJECT_ROOT / "requirements.txt"

    if not requirements.exists():
        log.error(f"Réparation impossible : requirements.txt introuvable ({requirements}).")
        return False

    if not venv_python.exists():
        log.warning(".venv absent : tentative de création automatique.")
        code, out, err = run(f'py -3 -m venv "{venv_dir}"', timeout=60)
        if code != 0:
            log.warning(f"Création via py -3 échouée : {err or out}")
            code, out, err = run(f'"{sys.executable}" -m venv "{venv_dir}"', timeout=60)

        if code != 0 or not venv_python.exists():
            log.error(f"Impossible de créer .venv automatiquement : {err or out}")
            return False

    log.info("Réparation automatique : installation des dépendances dans .venv...")
    code, out, err = run(
        f'"{venv_python}" -m pip install -r "{requirements}"',
        timeout=300,
    )
    if code != 0:
        log.error("Réparation automatique échouée pendant pip install.")
        if out:
            log.error(out)
        if err:
            log.error(err)
        return False

    log.info("Réparation automatique terminée.")
    return True


def resolve_backend_python() -> Path:
    configured = os.getenv("ERP_BACKEND_PYTHON") or os.getenv("BACKEND_PYTHON")
    candidates = []
    if configured:
        candidates.append(Path(configured))

    candidates.extend(
        [
            Path(sys.executable),
            PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
            PROJECT_ROOT / "venv_api" / "Scripts" / "python.exe",
            PROJECT_ROOT / ".venv-1" / "Scripts" / "python.exe",
        ]
    )

    required_modules = ["uvicorn", "fastapi", "sqlalchemy"]
    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)

        if python_has_modules(candidate, required_modules):
            log.info(f"Python backend sélectionné : {candidate}")
            return candidate

        log.warning(f"Python backend ignoré (dépendances manquantes ou Python invalide) : {candidate}")

    log.warning("Aucun environnement backend valide : tentative de réparation automatique.")
    if repair_project_env():
        venv_python = (PROJECT_ROOT / ".venv" / "Scripts" / "python.exe").resolve()
        if python_has_modules(venv_python, required_modules):
            log.info(f"Python backend sélectionné après réparation : {venv_python}")
            return venv_python

    required = ", ".join(required_modules)
    raise RuntimeError(
        "Aucun environnement Python backend valide n'a été trouvé après réparation. "
        f"Modules requis: {required}. "
        f"Commande manuelle: \"{PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'}\" "
        f"-m pip install -r \"{PROJECT_ROOT / 'requirements.txt'}\""
    )


def build_backend_cmd(dev_mode: bool = True) -> str:
    python_exe = resolve_backend_python()
    reload_arg = " --reload" if dev_mode else ""
    return (
        f'"{python_exe}" -m uvicorn backend.main:app '
        f"--host {BACKEND_HOST} --port {BACKEND_PORT}{reload_arg}"
    )


def cleanup_processes():
    if not settings.orchestrator_aggressive_cleanup:
        log.info(
            "Nettoyage agressif désactivé "
            "(ORCHESTRATOR_AGGRESSIVE_CLEANUP=0)."
        )
        return

    log.info("Nettoyage agressif des processus Python et PostgreSQL…")
    current_pid = os.getpid()

    # postgres.exe
    run("taskkill /IM postgres.exe /F")

    # python.exe sauf ce script
    code, out, err = run('wmic process where "name=\'python.exe\'" get ProcessId')
    if code == 0 and out:
        for line in out.splitlines():
            line = line.strip()
            if line.isdigit():
                pid = int(line)
                if pid != current_pid:
                    run(f"taskkill /PID {pid} /F")

    time.sleep(1)


def kill_port_5432():
    if not settings.orchestrator_allow_kill_port_5432:
        log.warning(
            "Kill des processus du port 5432 désactivé "
            "(ORCHESTRATOR_ALLOW_KILL_PORT_5432=0)."
        )
        return

    log.info("Nettoyage du port 5432…")
    cmd = r'for /f "tokens=5" %a in (\'netstat -ano ^| findstr :5432\') do taskkill /PID %a /F'
    run(cmd)
    time.sleep(1)


def port_5432_busy() -> bool:
    code, out, err = run("netstat -ano | findstr 5432")
    busy = bool(out.strip())
    log.info(f"Port 5432 occupé : {busy}")
    return busy


def postgres_state() -> str | None:
    code, out, err = run(f"sc query {POSTGRES_SERVICE}")
    if code != 0:
        log.error(f"Impossible de récupérer l’état PostgreSQL : {err or out}")
        return None
    for line in out.splitlines():
        if "STATE" in line:
            state = line.split()[-1]
            log.info(f"État PostgreSQL : {state}")
            return state
    return None


def start_postgres():
    log.info("Démarrage de PostgreSQL 18…")
    run(f"sc start {POSTGRES_SERVICE}")
    time.sleep(2)


def wait_for_postgres_ready(timeout: int = 20) -> bool:
    log.info("Attente de PostgreSQL (RUNNING)…")
    start = time.time()
    while time.time() - start < timeout:
        if postgres_state() == "RUNNING":
            log.info("PostgreSQL est RUNNING.")
            return True
        time.sleep(1)
    log.error("PostgreSQL ne passe pas à RUNNING dans le délai imparti.")
    return False


def quick_pg_ping(host: str = settings.db_host, port: int = POSTGRES_PORT, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def ensure_postgres_running(required: bool) -> bool:
    """Vérifie PostgreSQL et le démarre si le service est présent."""
    m_required = "obligatoire" if required else "optionnel"
    log.info(f"Vérification PostgreSQL ({m_required})…")

    state = postgres_state()
    if state is None:
        if required:
            log.error("PostgreSQL requis mais service introuvable ou inaccessible.")
            return False
        log.info("PostgreSQL non disponible, poursuite en base locale SQLite.")
        return True

    if state == "RUNNING":
        log.info("PostgreSQL déjà RUNNING.")
        return True

    if state == "STOPPED":
        log.info("PostgreSQL est STOPPED.")
        if port_5432_busy():
            log.info("Port 5432 occupé avant démarrage PostgreSQL.")
            kill_port_5432()
        start_postgres()
        return wait_for_postgres_ready()

    if state == "START_PENDING":
        log.info("PostgreSQL START_PENDING, attente…")
        return wait_for_postgres_ready()

    log.warning(f"État PostgreSQL non géré : {state}")
    return not required

# =========================
# TEST POSTGRESQL
# =========================

def test_psql_connection() -> bool:
    log.info("Test de connexion PostgreSQL via psql…")
    cmd = f'psql -U {POSTGRES_USER} -h {settings.db_host} -d {POSTGRES_DB} -c "SELECT 1;"'

    # If a password is configured via settings, use it non-interactively.
    if POSTGRES_PASSWORD:
        os.environ["PGPASSWORD"] = POSTGRES_PASSWORD
        code, out, err = run(cmd, timeout=10)
        if code == 0:
            log.info("Connexion PostgreSQL réussie.")
            return True
        log.error("Connexion PostgreSQL échouée.")
        if out:
            log.error(out)
        if err:
            log.error(err)
        return False

    # No password provided: prompt the user securely in Python and use it non-interactively.
    log.info("Aucun mot de passe PostgreSQL configuré: demande du mot de passe (entrée masquée)...")
    try:
        pwd = getpass.getpass(prompt="Mot de passe PostgreSQL: ")
    except Exception as e:
        log.error(f"Impossible de lire le mot de passe en entrée: {e}")
        return False

    if not pwd:
        log.error("Aucun mot de passe saisi.")
        return False

    # Use PGPASSWORD environment variable for non-interactive psql call
    os.environ["PGPASSWORD"] = pwd
    code, out, err = run(cmd, timeout=10)
    # remove the env var after use
    try:
        del os.environ["PGPASSWORD"]
    except KeyError:
        pass

    if code == 0:
        log.info("Connexion PostgreSQL réussie (mot de passe saisi).")
        return True
    log.error("Connexion PostgreSQL échouée (après saisie du mot de passe).")
    if out:
        log.error(out)
    if err:
        log.error(err)
    return False

# =========================
# BACKEND
# =========================

def wait_for_port(host: str, port: int, timeout: int = 20) -> bool:
    log.info(f"Attente de l’écoute sur {host}:{port}…")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                log.info(f"Port {port} joignable sur {host}.")
                return True
        except Exception:
            time.sleep(1)
    log.error(f"Port {port} non joignable sur {host} dans le délai imparti.")
    return False


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


_backend_process = None


def start_backend(dev_mode: bool = True):
    """Lance Uvicorn et conserve la référence du process pour un shutdown propre."""
    global _backend_process

    log.info("Lancement du backend API (Uvicorn)…")
    try:
        cmd = build_backend_cmd(dev_mode=dev_mode)
    except RuntimeError as exc:
        log.error(str(exc))
        raise

    log.info(f"Commande backend : {cmd}")

    _backend_process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=str(PROJECT_ROOT),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return _backend_process


def shutdown_backend(grace_seconds: int = 5):
    """Stoppe le backend Uvicorn démarré par start_backend().

    Objectif: éviter des consoles/process orphelins après fermeture de la GUI.
    """
    global _backend_process

    proc = _backend_process
    _backend_process = None

    if proc is None:
        log.info("shutdown_backend(): aucun process backend connu.")
        return

    try:
        if proc.poll() is None:
            log.info(f"shutdown_backend(): tentative stop backend (pid={proc.pid})…")
            proc.terminate()
            start = time.time()
            while time.time() - start < grace_seconds:
                if proc.poll() is not None:
                    break
                time.sleep(0.2)

        if proc.poll() is None:
            log.warning("shutdown_backend(): backend non stoppé après grace, kill…")
            proc.kill()

        log.info("shutdown_backend(): backend stoppé.")
    except Exception as e:
        log.error(f"shutdown_backend(): erreur lors du shutdown: {e}")


# =========================
# LOCKFILE
# =========================

def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    code, out, _ = run(f'tasklist /FI "PID eq {pid}"', timeout=5)
    return code == 0 and str(pid) in out


def acquire_lock() -> bool:
    if LOCKFILE_PATH.exists():
        try:
            pid = int(LOCKFILE_PATH.read_text(encoding="utf-8").strip())
        except Exception:
            pid = 0

        if is_pid_running(pid):
            log.error("Lockfile présent : un orchestrateur semble déjà actif.")
            return False

        log.warning("Lockfile périmé détecté, suppression automatique.")
        release_lock()

    try:
        LOCKFILE_PATH.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except Exception as e:
        log.error(f"Impossible de créer le lockfile : {e}")
        return False


def release_lock():
    try:
        if LOCKFILE_PATH.exists():
            LOCKFILE_PATH.unlink()
    except Exception as e:
        log.error(f"Impossible de supprimer le lockfile : {e}")

# =========================
# ORCHESTRATION (APPELÉE PAR L’ERP)
# =========================

def orchestrate(dev_mode: bool = True, progress_cb=None, message_cb=None) -> bool:
    """
    Orchestration complète, appelée depuis l’ERP.
    progress_cb(pourcentage:int) et message_cb(texte:str) sont optionnels.
    """
    def p(pct: int):
        if progress_cb:
            progress_cb(pct)

    def m(msg: str):
        if message_cb:
            message_cb(msg)
        log.info(msg)

    start_time = time.time()
    m("=== DÉMARRAGE ORCHESTRATION ERP ===")

    if not acquire_lock():
        m("Lockfile présent, arrêt.")
        return False

    try:
        p(5)
        m("Nettoyage des processus…")
        cleanup_processes()

        postgres_required = uses_postgres_master_db()
        p(15)
        if not ensure_postgres_running(required=postgres_required):
            m("PostgreSQL ne démarre pas.")
            return False

        if postgres_required:
            p(15)
            p(35)
            m("Ping rapide PostgreSQL…")
            if not quick_pg_ping():
                m("Ping PostgreSQL KO.")
                return False

            p(50)
            m("Test connexion PostgreSQL via psql…")
            if not test_psql_connection():
                m("Connexion PostgreSQL KO.")
                return False
        else:
            p(50)
            m("Base locale SQLite active : démarrage sans PostgreSQL.")

        p(65)
        m("Lancement backend API…")
        backend = None
        if is_port_open(BACKEND_HOST, BACKEND_PORT):
            m(f"Backend déjà disponible sur {BACKEND_HOST}:{BACKEND_PORT}, réutilisation.")
        else:
            try:
                backend = start_backend(dev_mode=dev_mode)
            except RuntimeError:
                m("Backend non lancé : environnement Python backend invalide.")
                return False

            if not wait_for_port(BACKEND_HOST, BACKEND_PORT):
                m("Backend non joignable, arrêt.")
                backend.terminate()
                return False

        p(90)
        m("Backend opérationnel. Préparation ERP…")

        duration = time.time() - start_time
        p(100)
        m(f"=== ORCHESTRATION OK (durée : {duration:.1f}s) ===")
        return True

    finally:
        release_lock()
