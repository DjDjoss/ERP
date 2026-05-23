from sqlalchemy.orm import Session
from modules.dossiers.models import Dossier
from modules.dossiers.schemas_dossier import DossierCreate
from modules.dossiers.services.create_database import create_dossier_database
from modules.dossiers.services.initialize_dossier import initialize_dossier
from modules.dossiers.utils import sanitize_db_name
from datetime import datetime
from sqlalchemy import func


# ---------------------------------------------------------
#  GÉNÉRATION DU NUMÉRO DE DOSSIER : AAMMNN (AVEC DEBUG)
# ---------------------------------------------------------
def generate_dossier_number(db: Session):
    now = datetime.now()
    year = now.strftime("%y")
    month = now.strftime("%m")

    print("DEBUG → now =", now)
    print("DEBUG → year =", year)
    print("DEBUG → month =", month)

    count = db.query(func.count(Dossier.id)).filter(
        func.date_trunc('month', Dossier.created_at) == func.date_trunc('month', func.now())
    ).scalar()

    print("DEBUG → count dossiers ce mois =", count)

    num = f"{count + 1:02d}"
    dossier_number = f"{year}{month}{num}"

    print("DEBUG → numéro généré =", dossier_number)

    return dossier_number


# ---------------------------------------------------------
#  CRÉATION DU DOSSIER (AVEC DEBUG)
# ---------------------------------------------------------
def create_dossier_service(data: DossierCreate, db: Session):
    print("DEBUG → Création dossier demandée avec :", data.dict())

    siren_clean = sanitize_db_name(data.siren.strip()) if data.siren else None

    if not siren_clean:
        import uuid
        siren_clean = f"gen{uuid.uuid4().hex[:6]}"

    print("DEBUG → siren_clean =", siren_clean)

    db_name = f"erp_{siren_clean}"
    print("DEBUG → db_name =", db_name)

    try:
        create_dossier_database(db_name)
        initialize_dossier(db_name)
    except Exception as e:
        raise Exception(f"Erreur création base '{db_name}': {e}")

    num_dossier = generate_dossier_number(db)
    print("DEBUG → num_dossier FINAL =", num_dossier)

    dossier = Dossier(
        num_dossier=num_dossier,
        siren=siren_clean,
        nic=data.nic,
        siret=data.siret,
        tva_intracom=data.tva_intracom,
        denomination=data.denomination or data.nom_entreprise or "Sans nom",
        nom_entreprise=data.nom_entreprise,
        voie=data.voie,
        hameau=data.hameau,
        complement=data.complement,
        cp=data.cp,
        ville=data.ville,
        region=data.region,
        pays=data.pays,
        tel=data.tel,
        port=data.port,
        email=data.email,
        web=data.web,
        responsable=data.responsable,
        responsable_tel=data.responsable_tel,
        responsable_email=data.responsable_email,
        forme_juridique=data.forme_juridique,
        frp=data.frp,
        cdi=data.cdi,
        service=data.service,
        naf=data.naf,
        naf_def=data.naf_def,
        rc=data.rc,
        capital=data.capital,
        parts=data.parts,
        type_dossier=data.type_dossier,
        regime_fiscal=data.regime_fiscal,
        imposition=data.imposition,
        regime_tva=data.regime_tva,
        tva2=data.tva2,
        database_name=db_name
    )

    db.add(dossier)
    db.commit()
    db.refresh(dossier)

    print("DEBUG → Dossier créé avec ID =", dossier.id)
    print("DEBUG → Dossier créé avec num_dossier =", dossier.num_dossier)

    return dossier
