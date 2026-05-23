# -*- coding: utf-8 -*-
"""
Service de chargement du Plan Comptable Général (PCG)

Charge le PCG français depuis un fichier texte/CSV
et l'insère dans la base de données.
"""

import csv
from typing import List, Dict, Optional
from decimal import Decimal
from sqlalchemy.orm import Session

from finance.models.core import AccountingAccount


class PCGLoaderError(Exception):
    """Exception pour les erreurs de chargement PCG"""
    pass


class PCGLoaderService:
    """
    Service de chargement du Plan Comptable Général
    
    Permet d'importer le PCG français standard
    dans un dossier comptable.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def load_from_file(
        self,
        dossier_id: int,
        file_path: str,
        overwrite: bool = False,
    ) -> Dict:
        """
        Charge le PCG depuis un fichier
        
        Args:
            dossier_id : ID du dossier
            file_path : Chemin du fichier PCG
            overwrite : Si True, supprime les comptes existants
            
        Returns:
            Dict : Statistiques de chargement
        """
        if overwrite:
            # Supprimer tous les comptes existants pour ce dossier
            self.db.query(AccountingAccount).filter(
                AccountingAccount.dossier_id == dossier_id
            ).delete()
            self.db.commit()
        
        stats = {
            "loaded": 0,
            "skipped": 0,
            "errors": [],
        }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            
            for row in reader:
                try:
                    account_number = row.get('N° du compte', '').strip()
                    if not account_number:
                        continue
                    
                    # Ignorer les lignes de titre/racines sans numéro valide
                    if not account_number[0].isdigit():
                        stats["skipped"] += 1
                        continue
                    
                    label = row.get('Intitulé', '').strip()
                    account_type = row.get('Type de compte', 'general').lower()
                    
                    # Déterminer la classe (premier chiffre)
                    account_class = account_number[0] if account_number else None
                    
                    # Déterminer si c'est un compte de tiers
                    is_third_party = account_class == '4' or 'third_party' in account_type
                    
                    # Vérifier si le compte existe déjà
                    existing = self.db.query(AccountingAccount).filter(
                        AccountingAccount.dossier_id == dossier_id,
                        AccountingAccount.number == account_number,
                    ).first()
                    
                    if existing:
                        stats["skipped"] += 1
                        continue
                    
                    # Créer le compte
                    account = AccountingAccount(
                        dossier_id=dossier_id,
                        number=account_number,
                        label=label,
                        account_class=account_class,
                        account_type=self._map_account_type(account_number, account_type),
                        is_active=True,
                        is_third_party=is_third_party,
                    )
                    
                    self.db.add(account)
                    stats["loaded"] += 1
                    
                except Exception as e:
                    stats["errors"].append(f"Ligne {reader.line_num}: {str(e)}")
        
        self.db.commit()
        return stats

    def _map_account_type(self, account_number: str, input_type: str) -> str:
        """Mappe le type de compte selon le numéro"""
        if not account_number:
            return "general"
        
        first_digit = account_number[0]
        
        # Mapping automatique selon la classe
        type_mapping = {
            '1': 'general',
            '2': 'general',
            '3': 'general',
            '4': 'third_party',
            '5': 'bank' if account_number.startswith('51') else 'cash',
            '6': 'general',
            '7': 'general',
        }
        
        # Types spécifiques
        if account_number.startswith('411'):
            return 'third_party_customer'
        elif account_number.startswith('401'):
            return 'third_party_supplier'
        elif account_number.startswith('512'):
            return 'bank'
        elif account_number.startswith('58'):
            return 'waiting'
        elif account_number.startswith(('44', '45')):
            return 'tax'
        
        return type_mapping.get(first_digit, 'general')

    def create_standard_journals(
        self,
        dossier_id: int,
        fiscal_year_id: Optional[int] = None,
    ) -> List:
        """
        Crée les journaux standards pour un dossier
        
        Returns:
            List : Journaux créés
        """
        from finance.models.core import AccountingJournal
        
        standard_journals = [
            {"code": "AC", "label": "Journal des achats", "type": "purchase"},
            {"code": "VE", "label": "Journal des ventes", "type": "sale"},
            {"code": "BQ", "label": "Journal de banque", "type": "bank"},
            {"code": "CA", "label": "Journal de caisse", "type": "cash"},
            {"code": "OD", "label": "Opérations diverses", "type": "general"},
            {"code": "AN", "label": "A-Nouveau", "type": "opening"},
        ]
        
        created = []
        for journal_data in standard_journals:
            existing = self.db.query(AccountingJournal).filter(
                AccountingJournal.dossier_id == dossier_id,
                AccountingJournal.code == journal_data["code"],
            ).first()
            
            if not existing:
                journal = AccountingJournal(
                    dossier_id=dossier_id,
                    fiscal_year_id=fiscal_year_id,
                    code=journal_data["code"],
                    label=journal_data["label"],
                    journal_type=journal_data["type"],
                    is_active=True,
                )
                self.db.add(journal)
                created.append(journal)
        
        self.db.commit()
        return created

    def get_pcg_summary(self, dossier_id: int) -> Dict:
        """Retourne un résumé du PCG chargé"""
        total = self.db.query(AccountingAccount).filter(
            AccountingAccount.dossier_id == dossier_id,
            AccountingAccount.is_active == True,
        ).count()
        
        by_class = {}
        for i in range(1, 8):
            count = self.db.query(AccountingAccount).filter(
                AccountingAccount.dossier_id == dossier_id,
                AccountingAccount.account_class == str(i),
                AccountingAccount.is_active == True,
            ).count()
            by_class[str(i)] = count
        
        return {
            "total_accounts": total,
            "by_class": by_class,
        }
