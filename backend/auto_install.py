import subprocess
import sys
import os

def install_dependencies():
    """Installe automatiquement les dépendances manquantes."""
    print("🔍 Vérification des dépendances...")
    
    # Liste des paquets critiques pour l'ERP
    packages = [
        "fastapi",
        "uvicorn[standard]",
        "sqlalchemy",
        "psycopg2-binary",
        "pydantic",
        "pydantic-settings",
        "httpx",
        "reportlab",
        "pandas",
        "openpyxl",
        "python-multipart",
        "jinja2"
    ]
    
    print(f"📦 Installation/Mise à jour de {len(packages)} paquets requis...")
    
    # Utilisation de pip via le python actuel pour garantir le bon venv
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir"] + packages
    
    try:
        subprocess.check_call(cmd)
        print("✅ Toutes les dépendances sont installées.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation : {e}")
        return False

if __name__ == "__main__":
    install_dependencies()