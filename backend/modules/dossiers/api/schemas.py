# ============================================================
#  SCHEMAS Pydantic — Dossiers
#  Version FULL-FIELDS compatible avec ton modèle SQLAlchemy.
# ============================================================

from pydantic import BaseModel, ConfigDict, field_validator


class DossierBase(BaseModel):
    num_dossier: str | None = None

    # Identité
    nom_entreprise: str | None = None
    siren: str | None = None
    nic: str | None = None
    siret: str | None = None
    tva_intracom: str | None = None

    # Adresse
    adresse1: str | None = None
    adresse2: str | None = None
    complement: str | None = None
    voie: str | None = None
    cp: str | None = None
    ville: str | None = None
    region: str | None = None
    pays: str | None = None

    # Contact
    tel_fixe: str | None = None
    tel_port: str | None = None
    email: str | None = None
    web: str | None = None
    resp_nom: str | None = None
    resp_tel: str | None = None
    resp_email: str | None = None

    # Juridique
    forme: str | None = None
    nom_commercial: str | None = None
    frp: str | None = None
    cdi: str | None = None
    service: str | None = None
    rc: str | None = None
    naf: str | None = None
    naf_def: str | None = None
    capital: str | None = None
    parts: str | None = None
    date_creation: str | None = None
    date_cloture: str | None = None

    # Fiscalité
    type_dossier: str | None = None
    regime_fiscal: str | None = None
    imposition: str | None = None
    regime_tva: str | None = None

    @field_validator("*", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class DossierCreate(DossierBase):
    pass


class DossierUpdate(DossierBase):
    pass


class Dossier(DossierBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
