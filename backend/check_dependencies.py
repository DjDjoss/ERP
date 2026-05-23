"""
============================================================
  Fichier : check_dependencies.py
  Projet  : ERP Rosan
  Rôle    : Vérification et installation automatique des dépendances
============================================================
"""

import subprocess
import sys
import importlib
from pathlib import Path

# Liste des dépendances critiques pour l'ERP
CRITICAL_DEPENDENCIES = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "psycopg2-binary",
    "pydantic",
    "httpx",
]

# Liste des dépendances optionnelles (fonctionnalités avancées)
OPTIONAL_DEPENDENCIES = [
    ("reportlab", "Exports PDF"),
    ("pandas", "Traitement de données"),
    ("openpyxl", "Exports Excel"),
    ("python-multipart", "Upload de fichiers"),
    ("jinja2", "Templates"),
    ("weasyprint", "PDF avancé"),
]

def check_package(package_name):
    """Vérifie si un package est installé."""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def install_package(package_name, version=None):
    """Installe un package avec pip."""
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]
        if version:
            cmd.append(f"{package_name}=={version}")
        else:
            cmd.append(package_name)
        
        print(f"📦 Installation de {package_name}...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {package_name} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec de l'installation de {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Vérifie et installe toutes les dépendances nécessaires."""
    print("\n" + "="*60)
    print("🔍 VÉRIFICATION DES DÉPENDANCES ERP ROSAN")
    print("="*60 + "\n")
    
    missing_critical = []
    missing_optional = []
    
    # Vérification des dépendances critiques
    print("📋 Vérification des dépendances CRITIQUES...")
    for package in CRITICAL_DEPENDENCIES:
        if check_package(package):
            print(f"  ✅ {package}")
        else:
            print(f"  ❌ {package} MANQUANT")
            missing_critical.append(package)
    
    # Vérification des dépendances optionnelles
    print("\n📋 Vérification des dépendances OPTIONNELLES...")
    for package, description in OPTIONAL_DEPENDENCIES:
        if check_package(package):
            print(f"  ✅ {package} ({description})")
        else:
            print(f"  ⚠️  {package} MANQUANT ({description})")
            missing_optional.append((package, description))
    
    # Installation des dépendances critiques manquantes
    if missing_critical:
        print(f"\n⚠️  {len(missing_critical)} dépendance(s) critique(s) manquante(s)")
        print("🔄 Installation en cours...\n")
        
        for package in missing_critical:
            if not install_package(package):
                print(f"\n❌ IMPOSSIBLE D'INSTALLER {package}")
                print("💡 Essayez manuellement: pip install {package}")
                return False
        
        print("\n✅ Toutes les dépendances critiques sont maintenant installées")
    
    # Proposition pour les dépendances optionnelles
    if missing_optional:
        print(f"\nℹ️  {len(missing_optional)} dépendance(s) optionnelle(s) manquante(s)")
        print("💡 Pour activer toutes les fonctionnalités, exécutez:")
        print(f"   pip install {' '.join([pkg for pkg, _ in missing_optional])}")
        
        # Installation automatique des optionnels courants
        common_optional = ["reportlab", "pandas", "openpyxl", "python-multipart"]
        to_install = [pkg for pkg, _ in missing_optional if pkg in common_optional]
        
        if to_install:
            print(f"\n🔄 Installation des optionnels courants: {', '.join(to_install)}")
            for package in to_install:
                install_package(package)
    
    print("\n" + "="*60)
    print("✅ VÉRIFICATION TERMINÉE")
    print("="*60 + "\n")
    
    return True

def create_requirements_file():
    """Crée un fichier requirements.txt à jour."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    
    all_packages = CRITICAL_DEPENDENCIES + [pkg for pkg, _ in OPTIONAL_DEPENDENCIES]
    
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write("# ============================================================\n")
        f.write("#  ERP ROSAN - Dépendances Python\n")
        f.write("# ============================================================\n\n")
        f.write("# Dépendances critiques\n")
        for pkg in CRITICAL_DEPENDENCIES:
            f.write(f"{pkg}\n")
        f.write("\n# Dépendances optionnelles (fonctionnalités avancées)\n")
        for pkg, _ in OPTIONAL_DEPENDENCIES:
            f.write(f"# {pkg}\n")
    
    print(f"📄 Fichier requirements.txt créé: {requirements_path}")

if __name__ == "__main__":
    success = check_and_install_dependencies()
    create_requirements_file()
    
    if success:
        print("\n🎉 L'ERP Rosan est prêt à démarrer !")
        print("🚀 Lancez le serveur avec: python -m uvicorn backend.main:app --reload")
    else:
        print("\n❌ Certaines dépendances critiques n'ont pas pu être installées")
        print("💡 Veuillez les installer manuellement avant de continuer")
        sys.exit(1)
