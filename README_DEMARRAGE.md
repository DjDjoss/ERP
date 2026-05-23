# 🚀 GUIDE DE DÉMARRAGE - ERP ROSAN

## ✅ PROBLÈME RÉSOLU : GESTION AUTOMATIQUE DES DÉPENDANCES

Le système vérifie et installe **automatiquement** les dépendances manquantes au démarrage.

---

## 📋 MÉTHODE 1 : Démarrage Automatique (Recommandé)

### Sur Windows :
```batch
# 1. Installation des dépendances (première utilisation uniquement)
install_dependencies.bat

# 2. Lancement de l'ERP
start_backend.bat
```

### Sur Linux/Mac :
```bash
# 1. Installation des dépendances (première utilisation uniquement)
chmod +x install_dependencies.sh
./install_dependencies.sh

# 2. Lancement de l'ERP
./start_backend.sh
```

---

## 📋 MÉTHODE 2 : Démarrage Manuel

```bash
# 1. Activer l'environnement virtuel
# Windows :
venv\Scripts\activate

# Linux/Mac :
source venv/bin/activate

# 2. Installer les dépendances (si nécessaire)
pip install -r backend/requirements.txt

# 3. Lancer le serveur
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🔍 VÉRIFICATION DU FONCTIONNEMENT

Une fois le serveur démarré, testez avec :

### Page d'accueil :
```bash
curl http://127.0.0.1:8000/
# Réponse attendue : {"message":"API ERP Rosan opérationnelle"}
```

### Documentation Swagger (interface web) :
```
http://127.0.0.1:8000/docs
```

### Fonctionnalités comptables :
```bash
curl http://127.0.0.1:8000/accounting/features
```

### Liste des dossiers :
```bash
curl http://127.0.0.1:8000/dossiers/
```

---

## 📦 DÉPENDANCES GÉRÉES AUTOMATIQUEMENT

### Critiques (installation automatique) :
- ✅ fastapi
- ✅ uvicorn
- ✅ sqlalchemy
- ✅ psycopg2-binary
- ✅ pydantic
- ✅ httpx

### Optionnelles (installation automatique) :
- ✅ reportlab (exports PDF)
- ✅ pandas (traitement données)
- ✅ openpyxl (exports Excel)
- ✅ python-multipart (upload fichiers)

---

## 🛠️ EN CAS DE PROBLÈME

### Erreur "ModuleNotFoundError" :
Le système devrait installer automatiquement le module manquant. Si ce n'est pas le cas :
```bash
pip install <nom_du_module>
```

### Port 8000 déjà utilisé :
```bash
# Windows :
taskkill /F /IM python.exe

# Linux/Mac :
pkill -f uvicorn
```

### Réinstallation complète :
```bash
# Supprimer l'environnement virtuel
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# Recréer et réinstaller
python -m venv venv
pip install -r backend/requirements.txt
```

---

## 📊 ENDPOINTS PRINCIPAUX

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Test de santé API |
| `/docs` | GET | Documentation Swagger UI |
| `/accounting/features` | GET | Catalogue fonctionnalités |
| `/dossiers/` | GET/POST | Gestion des dossiers entreprises |
| `/accounting/dossiers/{id}/journals` | GET | Journaux comptables |
| `/accounting/dossiers/{id}/accounts` | GET | Plan comptable |
| `/accounting/dossiers/{id}/entries` | GET/POST | Écritures comptables |

---

## 🎯 PROCHAINES ÉTAPES

1. ✅ Tester tous les endpoints via Swagger UI
2. ⚠️ Créer un dossier comptable de test
3. ⚠️ Initialiser les données de référence (bootstrap)
4. ⚠️ Saisir des écritures comptables
5. ⚠️ Générer des états financiers

---

**🎉 L'ERP Rosan est maintenant prêt à fonctionner !**
