import requests
from fastapi import HTTPException
from backend.settings import settings

TOKEN_URL = settings.insee_token_url
API_URL = settings.insee_api_url


def get_insee_token() -> str:
    """Obtient un token OAuth2 depuis l'INSEE."""
    if not settings.insee_client_id or not settings.insee_client_secret:
        raise HTTPException(503, "Configuration INSEE manquante")

    try:
        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(settings.insee_client_id, settings.insee_client_secret),
            timeout=8
        )
        response.raise_for_status()
        return response.json()["access_token"]

    except Exception as e:
        raise HTTPException(400, f"Erreur INSEE (token) : {e}")


def fetch_siren_data(siret: str) -> dict:
    """Récupère les données INSEE d'un établissement via son SIRET."""
    if len(siret) != 14:
        raise HTTPException(400, "Le SIRET doit contenir 14 chiffres")

    token = get_insee_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(
            API_URL + siret,
            headers=headers,
            timeout=8
        )
        response.raise_for_status()

    except Exception as e:
        raise HTTPException(400, f"Erreur INSEE (requête) : {e}")

    data = response.json().get("etablissement")
    if not data:
        raise HTTPException(404, "Établissement introuvable dans l’API INSEE")

    return data
