"""
Fixtures de données de test pour le module Dossiers
Données fournies pour tester toutes sortes de situations
"""

from datetime import date, timedelta
import random


def create_test_dossiers(session):
    """
    Crée plusieurs dossiers de test pour différentes situations
    """
    from dossiers.models import Dossier
    
    print("Création des dossiers de test...")
    
    dossiers_data = [
        {
            "nom_entreprise": "SARL TECHNOLOGIES AVENIR",
            "nom_commercial": "TechAvenir",
            "siren": "123456789",
            "siret": "12345678900012",
            "code_naf": "6201Z",
            "tva_intracom": "FR12345678901",
            "statut": "actif",
            "adresse": "15 Rue de la Innovation",
            "code_postal": "75001",
            "ville": "Paris",
            "pays": "France",
            "email": "contact@techavenir.fr",
            "telephone": "01 23 45 67 89",
            "site_web": "www.techavenir.fr",
            "forme_juridique": "SARL",
            "capital_social": 10000.00,
            "date_cloture_exercice": date(2024, 12, 31),
        },
        {
            "nom_entreprise": "EURL CONSULTING EXPERT",
            "nom_commercial": "ConsultExpert",
            "siren": "234567890",
            "siret": "23456789000023",
            "code_naf": "7022Z",
            "tva_intracom": "FR23456789012",
            "statut": "actif",
            "adresse": "42 Avenue des Champs-Élysées",
            "code_postal": "75008",
            "ville": "Paris",
            "pays": "France",
            "email": "info@consultexpert.fr",
            "telephone": "01 45 67 89 01",
            "site_web": "www.consultexpert.fr",
            "forme_juridique": "EURL",
            "capital_social": 5000.00,
            "date_cloture_exercice": date(2024, 12, 31),
        },
        {
            "nom_entreprise": "SA INDUSTRIE MANUFACTURE",
            "nom_commercial": "IndusManuf",
            "siren": "345678901",
            "siret": "34567890100034",
            "code_naf": "2562A",
            "tva_intracom": "FR34567890123",
            "statut": "actif",
            "adresse": "Zone Industrielle Nord",
            "code_postal": "69000",
            "ville": "Lyon",
            "pays": "France",
            "email": "contact@indusmanuf.fr",
            "telephone": "04 78 90 12 34",
            "site_web": "www.indusmanuf.fr",
            "forme_juridique": "SA",
            "capital_social": 100000.00,
            "date_cloture_exercice": date(2024, 6, 30),
        },
        {
            "nom_entreprise": "SCI IMMOBILIER PATRIMOINE",
            "nom_commercial": "ImmoPatrimoine",
            "siren": "456789012",
            "siret": "45678901200045",
            "code_naf": "6820A",
            "tva_intracom": "FR45678901234",
            "statut": "actif",
            "adresse": "8 Boulevard Haussmann",
            "code_postal": "75009",
            "ville": "Paris",
            "pays": "France",
            "email": "gestion@immopatrimoine.fr",
            "telephone": "01 56 78 90 12",
            "forme_juridique": "SCI",
            "capital_social": 20000.00,
            "date_cloture_exercice": date(2024, 12, 31),
        },
        {
            "nom_entreprise": "ASSOCIATION CULTURE LOISIRS",
            "nom_commercial": "CultureLoisirs",
            "siren": "567890123",
            "siret": "56789012300056",
            "code_naf": "9004Z",
            "tva_intracom": None,
            "statut": "actif",
            "adresse": "25 Rue du Théâtre",
            "code_postal": "33000",
            "ville": "Bordeaux",
            "pays": "France",
            "email": "contact@cultureloisirs.org",
            "telephone": "05 56 78 90 12",
            "forme_juridique": "Association",
            "capital_social": 0.00,
            "date_cloture_exercice": date(2024, 8, 31),
        },
    ]
    
    dossiers = []
    for dossier_data in dossiers_data:
        dossier = Dossier(**dossier_data)
        session.add(dossier)
        dossiers.append(dossier)
    
    session.commit()
    print(f"{len(dossiers)} dossiers créés avec succès!")
    
    return dossiers


def create_complete_dossier_with_finance(session, dossier_id):
    """
    Crée un dossier complet avec toutes les données finance associées
    Utilise les fixtures du module finance
    """
    from finance.fixtures.seed_data import create_complete_test_data
    
    # Récupérer le dossier pour avoir company_id et branch_id
    from dossiers.models import Dossier
    dossier = session.query(Dossier).filter(Dossier.id == dossier_id).first()
    
    if not dossier:
        raise ValueError(f"Dossier {dossier_id} non trouvé")
    
    # Pour l'instant, on utilise dossier_id comme company_id et branch_id
    # Dans une implémentation complète, il faudrait créer les tables Company et Branch
    return create_complete_test_data(
        session=session,
        dossier_id=dossier_id,
        company_id=dossier_id,
        branch_id=dossier_id
    )
