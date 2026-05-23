#!/bin/bash
# ============================================================
#   Fichier : install_dependencies.sh
#   Projet  : ERP Rosan
#   Rôle    : Installation automatique des dépendances Linux/Mac
# ============================================================

echo ""
echo "============================================================"
echo "  INSTALLATION DES DÉPENDANCES - ERP ROSAN"
echo "============================================================"
echo ""

# Vérification de Python
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python3 n'est pas installé ou n'est pas dans le PATH"
    echo "[INFO] Installez Python3 avec votre gestionnaire de paquets"
    exit 1
fi

echo "[OK] Python détecté: $(python3 --version)"
echo ""

# Activation de l'environnement virtuel si existant
if [ -d "venv" ]; then
    echo "[INFO] Activation de l'environnement virtuel..."
    source venv/bin/activate
else
    echo "[INFO] Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
fi

echo ""
echo "[INFO] Mise à jour de pip..."
pip install --upgrade pip

echo ""
echo "[INFO] Installation des dépendances depuis requirements.txt..."
pip install -r backend/requirements.txt

echo ""
echo "============================================================"
echo "  INSTALLATION TERMINÉE"
echo "============================================================"
echo ""
echo "Pour lancer l'ERP, exécutez:"
echo "   ./start_backend.sh"
echo ""
echo "Ou manuellement:"
echo "   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
echo ""
