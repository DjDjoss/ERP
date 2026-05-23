"""
============================================================
  Fichier : n8n_webhook.py
  Projet  : ERP Rosan
  Rôle    : Réception des données envoyées par n8n
============================================================
"""

from fastapi import APIRouter, Request

router = APIRouter()


# ============================================================
#  Route : /n8n-callback
#  Rôle  : Réception des données envoyées par n8n
# ============================================================
@router.post("/n8n-callback")
async def n8n_callback(request: Request):
    """
    Reçoit les données envoyées par un workflow n8n.
    """

    data = await request.json()

    print("[n8n → ERP] Données reçues :", data)

    return {"status": "reçu", "data": data}
