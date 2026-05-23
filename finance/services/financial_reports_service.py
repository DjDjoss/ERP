# -*- coding: utf-8 -*-
"""
Service des états financiers

Génère les rapports comptables :
- Balance générale
- Grand Livre
- Bilan
- Compte de résultat
- Tableau de flux de trésorerie
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from finance.models.entries import AccountingEntry, AccountingEntryLine
from finance.models.core import AccountingAccount, FiscalYear
from finance.models.reports import TrialBalance


class FinancialReportsService:
    """Service de génération des états financiers"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_trial_balance(
        self,
        dossier_id: int,
        fiscal_year_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[Dict]:
        """
        Génère la balance comptable
        
        Returns:
            List[Dict] : Liste des comptes avec soldes
        """
        # Déterminer la période
        fiscal_year = self.db.query(FiscalYear).get(fiscal_year_id)
        if not fiscal_year:
            raise ValueError(f"Exercice {fiscal_year_id} inexistant")
        
        if not date_from:
            date_from = fiscal_year.start_date
        if not date_to:
            date_to = fiscal_year.end_date
        
        # Récupérer tous les comptes actifs
        accounts = self.db.query(AccountingAccount).filter(
            AccountingAccount.dossier_id == dossier_id,
            AccountingAccount.is_active == True,
        ).order_by(AccountingAccount.number).all()
        
        balance = []
        for account in accounts:
            # Calculer les mouvements
            lines = self.db.query(AccountingEntryLine).join(
                AccountingEntry
            ).filter(
                AccountingEntryLine.account_id == account.id,
                AccountingEntry.dossier_id == dossier_id,
                AccountingEntry.entry_date >= date_from,
                AccountingEntry.entry_date <= date_to,
                AccountingEntry.status == 'posted',
            ).all()
            
            total_debit = sum(line.debit or Decimal('0') for line in lines)
            total_credit = sum(line.credit or Decimal('0') for line in lines)
            
            if total_debit > 0 or total_credit > 0:
                balance.append({
                    'account_number': account.number,
                    'account_label': account.label,
                    'debit': float(total_debit),
                    'credit': float(total_credit),
                    'balance': float(total_debit - total_credit),
                    'entry_count': len(lines),
                })
        
        return balance

    def get_general_ledger(
        self,
        dossier_id: int,
        account_number: str,
        date_from: date,
        date_to: date,
    ) -> List[Dict]:
        """
        Génère le grand livre pour un compte donné
        """
        account = self.db.query(AccountingAccount).filter(
            AccountingAccount.dossier_id == dossier_id,
            AccountingAccount.number.like(f"{account_number}%"),
        ).first()
        
        if not account:
            return []
        
        lines = self.db.query(AccountingEntryLine).join(
            AccountingEntry
        ).filter(
            AccountingEntryLine.account_id == account.id,
            AccountingEntry.dossier_id == dossier_id,
            AccountingEntry.entry_date >= date_from,
            AccountingEntry.entry_date <= date_to,
            AccountingEntry.status == 'posted',
        ).order_by(
            AccountingEntry.entry_date,
            AccountingEntry.entry_number,
            AccountingEntryLine.line_number,
        ).all()
        
        ledger = []
        cumulative = Decimal('0')
        
        for line in lines:
            cumulative += (line.debit or Decimal('0')) - (line.credit or Decimal('0'))
            ledger.append({
                'entry_date': line.entry.entry_date,
                'entry_number': line.entry.entry_number,
                'journal_code': line.entry.journal.code,
                'piece_number': line.entry.piece_number,
                'label': line.label or line.entry.label,
                'debit': float(line.debit or 0),
                'credit': float(line.credit or 0),
                'cumulative_balance': float(cumulative),
                'third_party': line.third_party_code,
            })
        
        return ledger

    def get_income_statement(
        self,
        dossier_id: int,
        fiscal_year_id: int,
    ) -> Dict:
        """
        Génère le compte de résultat (classes 6 et 7)
        """
        fiscal_year = self.db.query(FiscalYear).get(fiscal_year_id)
        
        charges = self._get_class_total(dossier_id, fiscal_year, '6')
        produits = self._get_class_total(dossier_id, fiscal_year, '7')
        
        result = produits - charges
        
        return {
            'total_charges': float(charges),
            'total_produits': float(produits),
            'resultat': float(result),
            'is_benefice': result >= 0,
        }

    def _get_class_total(
        self,
        dossier_id: int,
        fiscal_year: FiscalYear,
        account_class: str,
    ) -> Decimal:
        """Calcule le total d'une classe de comptes"""
        result = self.db.query(
            func.sum(AccountingEntryLine.debit + AccountingEntryLine.credit)
        ).join(
            AccountingEntry
        ).join(
            AccountingAccount
        ).filter(
            AccountingEntry.dossier_id == dossier_id,
            AccountingEntry.fiscal_year_id == fiscal_year.id,
            AccountingEntry.status == 'posted',
            AccountingAccount.account_class == account_class,
        ).scalar()
        
        return result or Decimal('0')
