"""
============================================================
  Fichier : test_n8n.py
  Projet  : ERP Rosan
  Rôle    : Route de test pour envoyer des données à n8n
============================================================
"""

from fastapi import APIRouter
from backend.modules.services.n8n_client import send_to_n8n

router = APIRouter()


# ============================================================
#  Route : /test-n8n
#  Rôle  : Envoie un payload simple vers un webhook n8n
# ============================================================
@router.get("/test-n8n")
def test_n8n():
    """
    Envoie un message de test vers un workflow n8n.
    """

    workflow_url = (
        "http://localhost:5678/webhook/TON_WEBHOOK_ID"
    )

    payload = {
        "message": "Hello depuis FastAPI",
        "status": "OK",
        "source": "ERP Python"
    }

    success = send_to_n8n(workflow_url, payload)

    return {"sent": success}
