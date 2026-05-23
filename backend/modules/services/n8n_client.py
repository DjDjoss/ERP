"""
============================================================
  Fichier : n8n_client.py
  Projet  : ERP Rosan
  Rôle    : Client HTTP pour envoyer des données à n8n
============================================================
"""

import requests


# ============================================================
#  Fonction : send_to_n8n
#  Rôle     : Envoie un dictionnaire Python vers un webhook n8n
#  Param    :
#      - workflow_url : URL du webhook n8n
#      - payload      : données à envoyer (dict)
#  Retour   : True si OK, False si erreur
# ============================================================
def send_to_n8n(workflow_url: str, payload: dict) -> bool:
    """
    Envoie un dictionnaire Python vers un webhook n8n.
    Retourne True si l'envoi est réussi, False sinon.
    """

    try:
        response = requests.post(workflow_url, json=payload)

        response.raise_for_status()
        return True

    except Exception as error:
        print("[ERREUR n8n] Impossible d'envoyer les données :", error)
        return False
