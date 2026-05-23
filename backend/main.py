"""
============================================================
  Fichier : main.py
  Projet  : ERP Rosan
  Rôle    : Point d'entrée principal de l'API FastAPI
============================================================
"""

# ============================================================
#  VÉRIFICATION ET INSTALLATION AUTOMATIQUE DES DÉPENDANCES
# ============================================================
import sys
import subprocess
from pathlib import Path

def ensure_dependencies():
    """Vérifie et installe automatiquement les dépendances manquantes."""
    critical_deps = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sqlalchemy": "sqlalchemy",
        "psycopg2": "psycopg2-binary",
        "pydantic": "pydantic",
        "httpx": "httpx",
        "reportlab": "reportlab",
        "pandas": "pandas",
        "openpyxl": "openpyxl",
    }
    
    missing = []
    for module_name, pip_name in critical_deps.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append((module_name, pip_name))
    
    if missing:
        print("\n" + "="*60)
        print("📦 INSTALLATION AUTOMATIQUE DES DÉPENDANCES")
        print("="*60)
        
        for module_name, pip_name in missing:
            print(f"⚠️  Module '{module_name}' manquant, installation...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
                print(f"✅ '{module_name}' installé avec succès")
            except subprocess.CalledProcessError as e:
                print(f"❌ Échec de l'installation de '{module_name}'")
                print(f"💡 Exécutez manuellement: pip install {pip_name}")
                sys.exit(1)
        
        print("\n✅ Toutes les dépendances sont maintenant installées\n")
        print("="*60 + "\n")

# Exécution de la vérification avant tout import
ensure_dependencies()

# ============================================================
#  LOGGING
# ============================================================
import logging

# ============================================================
#  IMPORTS FASTAPI
# ============================================================
from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ============================================================
#  IMPORTS ROUTES (MODULES INTERNES)
# ============================================================
#  ⚠️ IMPORTANT :
#  On respecte ton arborescence EXACTE :
#  E:\ERP_Rosan\backend\modules\dossiers\api\routes_dossiers.py
#  E:\ERP_Rosan\backend\routes\test_n8n.py
#  E:\ERP_Rosan\backend\routes\n8n_webhook.py
# ============================================================
from backend.modules.dossiers.api.routes_dossiers import router as dossiers_router
from backend.modules.accounting.api.routes_accounting import router as accounting_router
from backend.routes.n8n_webhook import router as n8n_webhook_router
from backend.routes.test_n8n import router as test_n8n_router
from backend.routes.events import router as events_router
from backend.connection_manager import init_master_db


# ============================================================
#  CONFIGURATION LOGGING
# ============================================================
logger = logging.getLogger("uvicorn.error")

# ============================================================
#  INITIALISATION DE L'APPLICATION FASTAPI
# ============================================================
app = FastAPI(title="ERP Rosan API", debug=True)
init_master_db()


# ============================================================
#  GESTION DES ERREURS PYDANTIC (VALIDATION)
# ============================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Intercepte les erreurs de validation Pydantic
    et renvoie une réponse JSON propre.
    """

    logger.error(f"Validation error for request {request.url} : " f"{exc.errors()}")

    return await request_validation_exception_handler(request, exc)


# ============================================================
#  MIDDLEWARE GLOBAL POUR CAPTURER TOUTES LES ERREURS
# ============================================================
@app.middleware("http")
async def catch_all_exceptions(request: Request, call_next):
    """
    Intercepte toutes les erreurs non gérées dans l'API.
    Permet d'éviter les crashs et d'avoir un retour propre.
    """

    try:
        response = await call_next(request)
        return response

    except Exception as error:
        logger.error(f"ERREUR NON GÉRÉE : {error}", exc_info=True)

        return JSONResponse(status_code=500, content={"detail": str(error)})


# ============================================================
#  CONFIGURATION CORS (AUTORISE TOUT)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes HTTP
    allow_headers=["*"],  # Autorise tous les headers
)

# ============================================================
#  INCLUSION DES ROUTES
# ============================================================

# Routes dossiers ERP
app.include_router(dossiers_router)

# Routes comptabilite ERP
app.include_router(accounting_router)

# Routes de test n8n
app.include_router(test_n8n_router)

# Routes callback n8n → ERP
app.include_router(n8n_webhook_router)

# Routes events SSE
app.include_router(events_router)



# ============================================================
#  ROUTE RACINE (TEST SIMPLE)
# ============================================================
@app.get("/")
def root():
    """
    Route simple pour vérifier que l'API fonctionne.
    """
    return {"message": "API ERP Rosan opérationnelle"}
