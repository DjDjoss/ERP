import subprocess
import sys
import os
import socket
import time


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_api():
    """Lance l'API sans bloquer l'interface ERP."""

    # Si l'API tourne déjà → OK
    if is_port_in_use(8000):
        return

    project_root = os.path.dirname(os.path.dirname(__file__))

    # On log les erreurs dans un fichier pour debug
    log_file = os.path.join(project_root, "api_log.txt")
    log = open(log_file, "w")

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--port",
            "8000"
        ],
        cwd=project_root,
        stdout=log,
        stderr=log,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

    # Attente courte
    for _ in range(10):
        if is_port_in_use(8000):
            return
        time.sleep(0.1)

    # Si on arrive ici → l'API n'a pas démarré
    return
