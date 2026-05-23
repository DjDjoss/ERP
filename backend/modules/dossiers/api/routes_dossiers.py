# ============================================================
#  ROUTES API — DOSSIERS
#  Version complète, corrigée, compatible avec ton projet :
#   ✔ GET liste
#   ✔ GET par ID
#   ✔ POST création
#   ✔ PUT mise à jour
#   ✔ DELETE suppression
#   ✔ PAPPERS : remplissage automatique
# ============================================================

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import requests
from requests import RequestException

# ------------------------------------------------------------
# IMPORTS CORRIGÉS POUR TON PROJET
# ------------------------------------------------------------
# Ton fichier database s'appelle "connection_manager.py"
from backend.connection_manager import get_db

# Modèles dans dossiers/
from backend.modules.dossiers import models
from backend.modules.accounting import models as accounting_models
from backend.modules.accounting.api.routes_accounting import bootstrap_accounting_data
from backend.events_manager import events_manager
from backend.routes.events import make_event


# Schémas dans dossiers/api/
from backend.modules.dossiers.api import schemas
from backend.settings import settings


router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


def _publish_dossier_changed(dossier_id: int | None, action: str) -> None:
    events_manager.publish_nowait(
        make_event(
            {
                "type": "dossier_changed",
                "dossier_id": dossier_id,
                "action": action,
            }
        )
    )


def _clean_payload(data: schemas.DossierBase, *, exclude_unset: bool = False) -> dict:
    return data.model_dump(exclude_unset=exclude_unset)


def _validate_dossier_payload(payload: dict) -> None:
    nom = payload.get("nom_entreprise")
    if "nom_entreprise" in payload and not nom:
        raise HTTPException(400, "Le nom de l'entreprise est obligatoire")

    siren = payload.get("siren")
    if siren and (not siren.isdigit() or len(siren) != 9):
        raise HTTPException(400, "SIREN invalide: 9 chiffres attendus")

    nic = payload.get("nic")
    if nic and (not nic.isdigit() or len(nic) != 5):
        raise HTTPException(400, "NIC invalide: 5 chiffres attendus")

    siret = payload.get("siret")
    if siret and (not siret.isdigit() or len(siret) != 14):
        raise HTTPException(400, "SIRET invalide: 14 chiffres attendus")


def _ensure_unique_siret(db: Session, siret: str | None, dossier_id: int | None = None) -> None:
    if not siret:
        return

    query = db.query(models.Dossier).filter(models.Dossier.siret == siret)
    if dossier_id is not None:
        query = query.filter(models.Dossier.id != dossier_id)

    if query.first():
        raise HTTPException(409, "Un dossier existe déjà avec ce SIRET")


def _assign_num_dossier(db: Session, dossier: models.Dossier) -> None:
    if dossier.num_dossier:
        return

    db.flush()
    dossier.num_dossier = f"DOS-{dossier.id:06d}"


def _build_mock_pappers_payload(siret: str) -> dict:
    siren = siret[:9]
    nic = siret[9:]
    return {
        "nom_entreprise": "ENTREPRISE DEMO MOCK",
        "siren": siren,
        "nic": nic,
        "siret": siret,
        "numero_tva_intracommunautaire": f"FR00{siren}",
        "siege": {
            "adresse_ligne_1": "1 RUE DE LA DEMO",
            "adresse_ligne_2": "",
            "complement_adresse": "",
            "voie": "RUE DE LA DEMO",
            "code_postal": "75001",
            "ville": "PARIS",
            "region": "Ile-de-France",
        },
        "telephone": "0102030405",
        "email": "contact@demo-mock.local",
        "site_web": "https://demo-mock.local",
        "forme_juridique": "SAS",
        "code_naf": "6201Z",
        "libelle_naf": "Programmation informatique",
        "date_creation": "2020-01-01",
        "numero_rcs": f"RCS PARIS {siren}",
        "capital": 10000,
    }


# ============================================================
# 1) LISTE DES DOSSIERS
# ============================================================
@router.get("/", response_model=list[schemas.Dossier])
def list_dossiers(db: Session = Depends(get_db)):
    """
    Renvoie la liste complète des dossiers.
    """
    return db.query(models.Dossier).order_by(models.Dossier.id.desc()).all()


# ============================================================
# 2) OBTENIR UN DOSSIER PAR ID
# ============================================================
@router.get("/{dossier_id}", response_model=schemas.Dossier)
def get_dossier(dossier_id: int, db: Session = Depends(get_db)):
    """
    Renvoie un dossier complet pour affichage ou modification.
    """
    dossier = db.query(models.Dossier).filter(models.Dossier.id == dossier_id).first()

    if not dossier:
        raise HTTPException(404, "Dossier introuvable")

    return dossier


# ============================================================
# 3) CRÉATION D’UN DOSSIER
# ============================================================
@router.post("/", response_model=schemas.Dossier)
def create_dossier(data: schemas.DossierCreate, db: Session = Depends(get_db)):
    """
    Crée un dossier avec TOUS les champs fournis.
    """
    payload = _clean_payload(data)
    _validate_dossier_payload(payload)

    if not payload.get("nom_entreprise"):
        raise HTTPException(400, "Le nom de l'entreprise est obligatoire")

    _ensure_unique_siret(db, payload.get("siret"))

    dossier = models.Dossier(**payload)

    db.add(dossier)
    _assign_num_dossier(db, dossier)
    db.commit()
    db.refresh(dossier)

    # Création dossier = initialisation immédiate de son plan comptable.
    # Le bootstrap ajoute les comptes manquants mais ne modifie jamais un compte existant,
    # ce qui préserve les personnalisations permanentes par dossier.
    bootstrap_accounting_data(db, dossier.id)
    db.refresh(dossier)
    _publish_dossier_changed(dossier.id, "created")

    return dossier


# ============================================================
# 4) MISE À JOUR D’UN DOSSIER
# ============================================================
@router.put("/{dossier_id}", response_model=schemas.Dossier)
def update_dossier(dossier_id: int, data: schemas.DossierUpdate, db: Session = Depends(get_db)):

    """
    Met à jour un dossier existant.
    Tous les champs sont mis à jour automatiquement.
    """
    dossier = db.query(models.Dossier).filter(models.Dossier.id == dossier_id).first()

    if not dossier:
        raise HTTPException(404, "Dossier introuvable")

    payload = _clean_payload(data, exclude_unset=True)
    _validate_dossier_payload(payload)
    _ensure_unique_siret(db, payload.get("siret"), dossier_id=dossier_id)

    for key, value in payload.items():
        setattr(dossier, key, value)

    db.commit()
    db.refresh(dossier)

    _publish_dossier_changed(dossier.id, "updated")

    return dossier


# ============================================================
# 5) SUPPRESSION D’UN DOSSIER
# ============================================================
@router.delete("/{dossier_id}")
def delete_dossier(dossier_id: int, db: Session = Depends(get_db)):
    """
    Supprime un dossier.
    """
    dossier = db.query(models.Dossier).filter(models.Dossier.id == dossier_id).first()

    if not dossier:
        raise HTTPException(404, "Dossier introuvable")

    entry_ids = [
        row.id
        for row in db.query(accounting_models.AccountingEntry.id)
        .filter(accounting_models.AccountingEntry.dossier_id == dossier_id)
        .all()
    ]
    if entry_ids:
        db.query(accounting_models.AccountingEntryLine).filter(
            accounting_models.AccountingEntryLine.entry_id.in_(entry_ids)
        ).delete(synchronize_session=False)

    db.query(accounting_models.AccountingEntry).filter_by(dossier_id=dossier_id).delete()
    db.query(accounting_models.AccountingFiscalYear).filter_by(dossier_id=dossier_id).delete()
    db.query(accounting_models.AccountingJournal).filter_by(dossier_id=dossier_id).delete()
    db.query(accounting_models.AccountingAccount).filter_by(dossier_id=dossier_id).delete()

    db.delete(dossier)
    db.commit()
    _publish_dossier_changed(dossier_id, "deleted")

    return {"message": "Dossier supprimé"}


# ============================================================
# 6) PAPPERS — REMPLISSAGE AUTOMATIQUE
# ============================================================

@router.get("/from-pappers/{siret}")
def get_from_pappers(siret: str):
    """
    Récupère les données Pappers pour un SIRET
    et renvoie un JSON FULL-FIELDS compatible avec le frontend.
    """

    if not siret.isdigit() or len(siret) != 14:
        raise HTTPException(400, "SIRET invalide: 14 chiffres attendus")

    if settings.pappers_mock_mode:
        p = _build_mock_pappers_payload(siret)
    else:
        if not settings.pappers_api_key:
            raise HTTPException(
                503,
                "Configuration Pappers manquante: ajoutez PAPPERS_API_KEY dans .env.local "
                "ou activez PAPPERS_MOCK_MODE=1 pour les tests.",
            )

        try:
            r = requests.get(
                settings.pappers_base_url,
                params={"api_token": settings.pappers_api_key, "siret": siret},
                timeout=settings.pappers_timeout_seconds,
            )
        except requests.Timeout as exc:
            raise HTTPException(502, "Timeout API Pappers") from exc
        except RequestException as exc:
            raise HTTPException(502, "API Pappers indisponible") from exc

        if r.status_code == 401:
            raise HTTPException(
                401,
                "Clé API Pappers refusée. Vérifiez que PAPPERS_API_KEY est correcte, "
                "active dans votre espace Pappers API, et que le compte dispose de crédits.",
            )

        if r.status_code != 200:
            raise HTTPException(502, f"Erreur API Pappers (status {r.status_code})")

        try:
            p = r.json()
        except ValueError as exc:
            raise HTTPException(502, "Réponse Pappers invalide (JSON)") from exc

    # ------------------------------------------------------------
    # MAPPING PAPPERS → ERP FULL-FIELDS
    # ------------------------------------------------------------
    data = {
        # Identité
        "nom_entreprise": p.get("nom_entreprise"),
        "siren": p.get("siren"),
        "nic": p.get("nic"),
        "siret": p.get("siret"),
        "tva_intracom": p.get("numero_tva_intracommunautaire"),

        # Adresse
        "adresse1": p.get("siege", {}).get("adresse_ligne_1"),
        "adresse2": p.get("siege", {}).get("adresse_ligne_2"),
        "complement": p.get("siege", {}).get("complement_adresse"),
        "voie": p.get("siege", {}).get("voie"),
        "cp": p.get("siege", {}).get("code_postal"),
        "ville": p.get("siege", {}).get("ville"),
        "region": p.get("siege", {}).get("region"),
        "pays": "France",

        # Contact
        "tel_fixe": p.get("telephone"),
        "email": p.get("email"),
        "web": p.get("site_web"),

        # Juridique
        "forme": p.get("forme_juridique"),
        "naf": p.get("code_naf"),
        "naf_def": p.get("libelle_naf"),
        "date_creation": p.get("date_creation"),
        "rc": p.get("numero_rcs"),
        "capital": p.get("capital"),
    }

    return data
