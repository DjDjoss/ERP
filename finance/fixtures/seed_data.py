"""
Fixtures de données de test pour le module Finance
Données fournies pour tester toutes sortes de situations comptables
"""

from datetime import date, timedelta
from decimal import Decimal
import random


def create_complete_test_data(session, dossier_id, company_id, branch_id):
    """
    Crée un jeu de données complet pour tester le module finance
    Inclut: exercices, journaux, comptes, écritures, lettrages, banques, etc.
    """
    
    # Import des modèles
    from finance.models.core import FiscalYear, Journal, Account, AnalyticSection, AnalyticAxis
    from finance.models.entries import JournalEntry, JournalEntryLine
    from finance.models.treasury import BankAccount, BankTransaction, BankReconciliation
    from finance.models.assets import Asset, AssetDepreciation
    from finance.models.reports import TrialBalanceLine, ReportTemplate
    
    print(f"Création des données de test pour le dossier {dossier_id}...")
    
    # ========================================================================
    # 1. EXERCICES COMPTABLES
    # ========================================================================
    fiscal_years = []
    for year_offset in [-1, 0, 1]:
        year = 2024 + year_offset
        fy = FiscalYear(
            name=f"Exercice {year}",
            start_date=date(year, 1, 1),
            end_date=date(year, 12, 31),
            status="closed" if year_offset < 0 else "current" if year_offset == 0 else "open",
            company_id=company_id,
            branch_id=branch_id,
            dossier_id=dossier_id
        )
        session.add(fy)
        fiscal_years.append(fy)
    
    session.flush()
    current_fy = fiscal_years[1]  # Exercice 2024
    
    # ========================================================================
    # 2. JOURNAUX COMPTABLES
    # ========================================================================
    journals_data = [
        {"code": "VT", "name": "Journal des Ventes", "type": "sale"},
        {"code": "AC", "name": "Journal des Achats", "type": "purchase"},
        {"code": "BQ", "name": "Journal de Banque", "type": "bank"},
        {"code": "CA", "name": "Journal de Caisse", "type": "cash"},
        {"code": "OD", "name": "Opérations Diverses", "type": "general"},
        {"code": "AN", "name": "Journal d'Analytique", "type": "analytic"},
        {"code": "AS", "name": "Journal des Immobilisations", "type": "asset"},
        {"code": "PA", "name": "Journal de Paie", "type": "payroll"},
    ]
    
    journals = {}
    for jd in journals_data:
        journal = Journal(
            code=jd["code"],
            name=jd["name"],
            journal_type=jd["type"],
            fiscal_year_id=current_fy.id,
            company_id=company_id,
            branch_id=branch_id,
            is_active=True
        )
        session.add(journal)
        journals[jd["code"]] = journal
    
    session.flush()
    
    # ========================================================================
    # 3. PLAN COMPTABLE COMPLET (PCG)
    # ========================================================================
    accounts_data = [
        # Classe 1 - Capitaux
        {"number": "101000", "name": "Capital social", "type": "equity"},
        {"number": "106100", "name": "Réserve légale", "type": "equity"},
        {"number": "110000", "name": "Report à nouveau", "type": "equity"},
        {"number": "120000", "name": "Résultat de l'exercice", "type": "equity"},
        
        # Classe 2 - Immobilisations
        {"number": "205000", "name": "Concessions et droits similaires", "type": "asset_fixed"},
        {"number": "213500", "name": "Matériel informatique", "type": "asset_fixed"},
        {"number": "218300", "name": "Mobilier de bureau", "type": "asset_fixed"},
        {"number": "281350", "name": "Amortissement matériel informatique", "type": "depreciation"},
        {"number": "281830", "name": "Amortissement mobilier", "type": "depreciation"},
        
        # Classe 3 - Stocks
        {"number": "370000", "name": "Stock de marchandises", "type": "stock"},
        
        # Classe 4 - Tiers
        {"number": "401000", "name": "Fournisseurs", "type": "liability"},
        {"number": "401ABC", "name": "Fournisseur ABC", "type": "liability", "parent": "401000"},
        {"number": "401XYZ", "name": "Fournisseur XYZ", "type": "liability", "parent": "401000"},
        {"number": "411000", "name": "Clients", "type": "asset"},
        {"number": "411CLI01", "name": "Client DUPONT", "type": "asset", "parent": "411000"},
        {"number": "411CLI02", "name": "Client MARTIN", "type": "asset", "parent": "411000"},
        {"number": "411CLI03", "name": "Client BERNARD", "type": "asset", "parent": "411000"},
        {"number": "445660", "name": "TVA déductible", "type": "liability"},
        {"number": "445710", "name": "TVA collectée", "type": "liability"},
        {"number": "445510", "name": "TVA à décaisser", "type": "liability"},
        {"number": "421000", "name": "Personnel - Rémunérations dues", "type": "liability"},
        {"number": "431000", "name": "Sécurité sociale", "type": "liability"},
        {"number": "441000", "name": "Organismes sociaux", "type": "liability"},
        {"number": "444000", "name": "État - Impôts sur les bénéfices", "type": "liability"},
        
        # Classe 5 - Financier
        {"number": "512000", "name": "Banque", "type": "bank"},
        {"number": "512BPCE", "name": "Banque Populaire", "type": "bank", "parent": "512000"},
        {"number": "512SGFR", "name": "Société Générale", "type": "bank", "parent": "512000"},
        {"number": "531000", "name": "Caisse EUR", "type": "cash"},
        {"number": "580000", "name": "Virements internes", "type": "transfer"},
        
        # Classe 6 - Charges
        {"number": "607000", "name": "Achats de marchandises", "type": "expense"},
        {"number": "611000", "name": "Sous-traitance générale", "type": "expense"},
        {"number": "613500", "name": "Locations mobilières", "type": "expense"},
        {"number": "615200", "name": "Entretien et réparations", "type": "expense"},
        {"number": "616200", "name": "Primes d'assurances", "type": "expense"},
        {"number": "622000", "name": "Rémunérations d'intermédiaires", "type": "expense"},
        {"number": "622600", "name": "Honoraires", "type": "expense"},
        {"number": "623100", "name": "Annonces et insertions", "type": "expense"},
        {"number": "625100", "name": "Voyages et déplacements", "type": "expense"},
        {"number": "625600", "name": "Missions", "type": "expense"},
        {"number": "626100", "name": "Frais d'affranchissement", "type": "expense"},
        {"number": "627200", "name": "Commissions et frais sur émission d'emprunts", "type": "expense"},
        {"number": "627800", "name": "Autres frais financiers", "type": "expense"},
        {"number": "635100", "name": "Impôts directs", "type": "expense"},
        {"number": "635400", "name": "Autres impôts et taxes", "type": "expense"},
        {"number": "641100", "name": "Salaires, appointements", "type": "expense"},
        {"number": "641300", "name": "Primes et gratifications", "type": "expense"},
        {"number": "645100", "name": "Cotisations à l'URSSAF", "type": "expense"},
        {"number": "645300", "name": "Cotisations aux caisses de retraites", "type": "expense"},
        {"number": "648000", "name": "Autres charges de personnel", "type": "expense"},
        {"number": "661100", "name": "Intérêts des emprunts et dettes", "type": "expense"},
        {"number": "671100", "name": "Pénalités sur marchés", "type": "expense"},
        {"number": "671800", "name": "Dons, libéralités", "type": "expense"},
        
        # Classe 7 - Produits
        {"number": "706000", "name": "Prestations de services", "type": "income"},
        {"number": "707000", "name": "Ventes de marchandises", "type": "income"},
        {"number": "708000", "name": "Produits des activités annexes", "type": "income"},
        {"number": "752000", "name": "Revenus des immeubles non affectés", "type": "income"},
        {"number": "761000", "name": "Produits de participations", "type": "income"},
        {"number": "768000", "name": "Autres produits financiers", "type": "income"},
        {"number": "771000", "name": "Produits exceptionnels sur opérations de gestion", "type": "income"},
        {"number": "775000", "name": "Produits des cessions d'éléments d'actif", "type": "income"},
    ]
    
    accounts = {}
    for acc_data in accounts_data:
        account = Account(
            number=acc_data["number"],
            name=acc_data["name"],
            account_type=acc_data["type"],
            fiscal_year_id=current_fy.id,
            company_id=company_id,
            branch_id=branch_id,
            is_active=True,
            parent_account_id=None
        )
        session.add(account)
        accounts[acc_data["number"]] = account
    
    session.flush()
    
    # Gestion des comptes parents
    for acc_data in accounts_data:
        if "parent" in acc_data:
            child_acc = accounts[acc_data["number"]]
            parent_acc = accounts[acc_data["parent"]]
            child_acc.parent_account_id = parent_acc.id
    
    session.flush()
    
    # ========================================================================
    # 4. COMPTES ANALYTIQUES
    # ========================================================================
    axes_data = [
        {"code": "DEPT", "name": "Départements"},
        {"code": "PROJ", "name": "Projets"},
        {"code": "PROD", "name": "Produits"},
    ]
    
    analytic_axes = {}
    for axis_data in axes_data:
        axis = AnalyticAxis(
            code=axis_data["code"],
            name=axis_data["name"],
            fiscal_year_id=current_fy.id,
            company_id=company_id,
            branch_id=branch_id,
            is_active=True
        )
        session.add(axis)
        analytic_axes[axis_data["code"]] = axis
    
    session.flush()
    
    sections_data = [
        {"axis": "DEPT", "code": "ADM", "name": "Administration"},
        {"axis": "DEPT", "code": "COM", "name": "Commercial"},
        {"axis": "DEPT", "code": "DEV", "name": "Développement"},
        {"axis": "DEPT", "code": "RH", "name": "Ressources Humaines"},
        {"axis": "PROJ", "code": "PRJ001", "name": "Projet Alpha"},
        {"axis": "PROJ", "code": "PRJ002", "name": "Projet Beta"},
        {"axis": "PROJ", "code": "PRJ003", "name": "Projet Gamma"},
        {"axis": "PROD", "code": "SRV01", "name": "Service Conseil"},
        {"axis": "PROD", "code": "SRV02", "name": "Service Formation"},
        {"axis": "PROD", "code": "SRV03", "name": "Service Maintenance"},
    ]
    
    analytic_sections = {}
    for sec_data in sections_data:
        section = AnalyticSection(
            code=sec_data["code"],
            name=sec_data["name"],
            axis_id=analytic_axes[sec_data["axis"]].id,
            fiscal_year_id=current_fy.id,
            company_id=company_id,
            branch_id=branch_id,
            is_active=True
        )
        session.add(section)
        analytic_sections[sec_data["code"]] = section
    
    session.flush()
    
    # ========================================================================
    # 5. ÉCRITURES COMPTABLES DIVERSES
    # ========================================================================
    
    # Écriture de constitution du capital
    entry_capital = JournalEntry(
        journal_id=journals["OD"].id,
        fiscal_year_id=current_fy.id,
        entry_date=date(2024, 1, 5),
        document_date=date(2024, 1, 5),
        reference="CONSTIT-001",
        description="Constitution du capital social",
        is_posted=True,
        company_id=company_id,
        branch_id=branch_id
    )
    session.add(entry_capital)
    session.flush()
    
    line_capital_debit = JournalEntryLine(
        entry_id=entry_capital.id,
        account_id=accounts["512000"].id,
        debit=Decimal("50000.00"),
        credit=Decimal("0.00"),
        description="Souscription capital",
        company_id=company_id,
        branch_id=branch_id
    )
    line_capital_credit = JournalEntryLine(
        entry_id=entry_capital.id,
        account_id=accounts["101000"].id,
        debit=Decimal("0.00"),
        credit=Decimal("50000.00"),
        description="Capital social",
        company_id=company_id,
        branch_id=branch_id
    )
    session.add_all([line_capital_debit, line_capital_credit])
    
    # Écritures de ventes (10 factures)
    for i in range(1, 11):
        client_num = (i % 3) + 1
        client_code = f"411CLI0{client_num}"
        amount_ht = Decimal(str(random.uniform(500, 5000)))
        tva_rate = Decimal("0.20")
        tva_amount = amount_ht * tva_rate
        amount_ttc = amount_ht + tva_amount
        
        entry_sale = JournalEntry(
            journal_id=journals["VT"].id,
            fiscal_year_id=current_fy.id,
            entry_date=date(2024, 1, 10) + timedelta(days=i*3),
            document_date=date(2024, 1, 10) + timedelta(days=i*3),
            reference=f"FAC-2024-{i:04d}",
            description=f"Facture client {client_num}",
            is_posted=True,
            company_id=company_id,
            branch_id=branch_id
        )
        session.add(entry_sale)
        session.flush()
        
        lines = [
            JournalEntryLine(
                entry_id=entry_sale.id,
                account_id=accounts[client_code].id,
                debit=amount_ttc,
                credit=Decimal("0.00"),
                description=f"Facture {i} - Client {client_num}",
                company_id=company_id,
                branch_id=branch_id
            ),
            JournalEntryLine(
                entry_id=entry_sale.id,
                account_id=accounts["706000"].id,
                debit=Decimal("0.00"),
                credit=amount_ht,
                description=f"Chiffre d'affaires HT",
                company_id=company_id,
                branch_id=branch_id
            ),
            JournalEntryLine(
                entry_id=entry_sale.id,
                account_id=accounts["445710"].id,
                debit=Decimal("0.00"),
                credit=tva_amount,
                description=f"TVA collectée 20%",
                company_id=company_id,
                branch_id=branch_id
            ),
        ]
        session.add_all(lines)
    
    # Écritures d'achats (8 factures)
    for i in range(1, 9):
        supplier_code = "401ABC" if i % 2 == 0 else "401XYZ"
        amount_ht = Decimal(str(random.uniform(200, 3000)))
        tva_rate = Decimal("0.20")
        tva_amount = amount_ht * tva_rate
        amount_ttc = amount_ht + tva_amount
        
        entry_purchase = JournalEntry(
            journal_id=journals["AC"].id,
            fiscal_year_id=current_fy.id,
            entry_date=date(2024, 1, 15) + timedelta(days=i*4),
            document_date=date(2024, 1, 15) + timedelta(days=i*4),
            reference=f"FAC-FOUR-{i:04d}",
            description=f"Facture fournisseur {i}",
            is_posted=True,
            company_id=company_id,
            branch_id=branch_id
        )
        session.add(entry_purchase)
        session.flush()
        
        lines = [
            JournalEntryLine(
                entry_id=entry_purchase.id,
                account_id=accounts["611000"].id,
                debit=amount_ht,
                credit=Decimal("0.00"),
                description=f"Achat HT",
                company_id=company_id,
                branch_id=branch_id
            ),
            JournalEntryLine(
                entry_id=entry_purchase.id,
                account_id=accounts["445660"].id,
                debit=tva_amount,
                credit=Decimal("0.00"),
                description=f"TVA déductible 20%",
                company_id=company_id,
                branch_id=branch_id
            ),
            JournalEntryLine(
                entry_id=entry_purchase.id,
                account_id=accounts[supplier_code].id,
                debit=Decimal("0.00"),
                credit=amount_ttc,
                description=f"Dettes fournisseurs",
                company_id=company_id,
                branch_id=branch_id
            ),
        ]
        session.add_all(lines)
    
    # Écritures de banque (débits et crédits)
    for i in range(1, 16):
        is_debit = i % 2 == 0
        amount = Decimal(str(random.uniform(100, 2000)))
        
        entry_bank = JournalEntry(
            journal_id=journals["BQ"].id,
            fiscal_year_id=current_fy.id,
            entry_date=date(2024, 2, 1) + timedelta(days=i*2),
            document_date=date(2024, 2, 1) + timedelta(days=i*2),
            reference=f"BQ-2024-{i:04d}",
            description=f"Opération bancaire {i}",
            is_posted=True,
            company_id=company_id,
            branch_id=branch_id
        )
        session.add(entry_bank)
        session.flush()
        
        if is_debit:
            lines = [
                JournalEntryLine(
                    entry_id=entry_bank.id,
                    account_id=accounts["512000"].id,
                    debit=amount,
                    credit=Decimal("0.00"),
                    description="Encaissement",
                    company_id=company_id,
                    branch_id=branch_id
                ),
                JournalEntryLine(
                    entry_id=entry_bank.id,
                    account_id=accounts["411CLI01"].id,
                    debit=Decimal("0.00"),
                    credit=amount,
                    description="Règlement client",
                    company_id=company_id,
                    branch_id=branch_id
                ),
            ]
        else:
            lines = [
                JournalEntryLine(
                    entry_id=entry_bank.id,
                    account_id=accounts["401ABC"].id,
                    debit=amount,
                    credit=Decimal("0.00"),
                    description="Règlement fournisseur",
                    company_id=company_id,
                    branch_id=branch_id
                ),
                JournalEntryLine(
                    entry_id=entry_bank.id,
                    account_id=accounts["512000"].id,
                    debit=Decimal("0.00"),
                    credit=amount,
                    description="Décaissement",
                    company_id=company_id,
                    branch_id=branch_id
                ),
            ]
        session.add_all(lines)
    
    # Écriture d'amortissement
    entry_amort = JournalEntry(
        journal_id=journals["AS"].id,
        fiscal_year_id=current_fy.id,
        entry_date=date(2024, 12, 31),
        document_date=date(2024, 12, 31),
        reference="AMORT-2024",
        description="Dotations aux amortissements 2024",
        is_posted=True,
        company_id=company_id,
        branch_id=branch_id
    )
    session.add(entry_amort)
    session.flush()
    
    amort_amount = Decimal("2500.00")
    lines_amort = [
        JournalEntryLine(
            entry_id=entry_amort.id,
            account_id=accounts["627200"].id,
            debit=amort_amount,
            credit=Decimal("0.00"),
            description="Dotation amortissement",
            company_id=company_id,
            branch_id=branch_id
        ),
        JournalEntryLine(
            entry_id=entry_amort.id,
            account_id=accounts["281350"].id,
            debit=Decimal("0.00"),
            credit=amort_amount,
            description="Amortissement cumulé",
            company_id=company_id,
            branch_id=branch_id
        ),
    ]
    session.add_all(lines_amort)
    
    # Écriture de régularisation TVA
    entry_tva = JournalEntry(
        journal_id=journals["OD"].id,
        fiscal_year_id=current_fy.id,
        entry_date=date(2024, 12, 31),
        document_date=date(2024, 12, 31),
        reference="TVA-DEC-2024",
        description="Régularisation TVA décembre 2024",
        is_posted=True,
        company_id=company_id,
        branch_id=branch_id
    )
    session.add(entry_tva)
    session.flush()
    
    tva_collectee = Decimal("15000.00")
    tva_deductible = Decimal("8000.00")
    tva_a_payer = tva_collectee - tva_deductible
    
    lines_tva = [
        JournalEntryLine(
            entry_id=entry_tva.id,
            account_id=accounts["445710"].id,
            debit=tva_collectee,
            credit=Decimal("0.00"),
            description="Solde TVA collectée",
            company_id=company_id,
            branch_id=branch_id
        ),
        JournalEntryLine(
            entry_id=entry_tva.id,
            account_id=accounts["445660"].id,
            debit=Decimal("0.00"),
            credit=tva_deductible,
            description="Solde TVA déductible",
            company_id=company_id,
            branch_id=branch_id
        ),
        JournalEntryLine(
            entry_id=entry_tva.id,
            account_id=accounts["445510"].id,
            debit=Decimal("0.00"),
            credit=tva_a_payer,
            description="TVA à décaisser",
            company_id=company_id,
            branch_id=branch_id
        ),
    ]
    session.add_all(lines_tva)
    
    session.commit()
    print("Données de test créées avec succès!")
    
    return {
        "fiscal_years": fiscal_years,
        "journals": journals,
        "accounts": accounts,
        "analytic_axes": analytic_axes,
        "analytic_sections": analytic_sections,
    }
