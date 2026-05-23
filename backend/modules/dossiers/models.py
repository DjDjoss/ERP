# ============================================================
#  MODEL SQLAlchemy — Dossier
#  Version FULL-FIELDS alignée avec schemas.py
# ============================================================

from sqlalchemy import Column, Integer, String
from backend.connection_manager import Base


class Dossier(Base):
    __tablename__ = "dossiers"

    id = Column(Integer, primary_key=True, index=True)
    num_dossier = Column(String, index=True)

    # Identité
    nom_entreprise = Column(String)
    siren = Column(String)
    nic = Column(String)
    siret = Column(String)
    tva_intracom = Column(String)

    # Adresse
    adresse1 = Column(String)
    adresse2 = Column(String)
    complement = Column(String)
    voie = Column(String)
    cp = Column(String)
    ville = Column(String)
    region = Column(String)
    pays = Column(String)

    # Contact
    tel_fixe = Column(String)
    tel_port = Column(String)
    email = Column(String)
    web = Column(String)
    resp_nom = Column(String)
    resp_tel = Column(String)
    resp_email = Column(String)

    # Juridique
    forme = Column(String)
    nom_commercial = Column(String)
    frp = Column(String)
    cdi = Column(String)
    service = Column(String)
    rc = Column(String)
    naf = Column(String)
    naf_def = Column(String)
    capital = Column(String)
    parts = Column(String)
    date_creation = Column(String)
    date_cloture = Column(String)

    # Fiscalité
    type_dossier = Column(String)
    regime_fiscal = Column(String)
    imposition = Column(String)
    regime_tva = Column(String)
