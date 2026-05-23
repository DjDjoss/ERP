# -*- coding: utf-8 -*-
"""
Service de rapprochement bancaire

Permet de rapprocher les transactions bancaires
avec les écritures comptables.
"""

from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from finance.models.treasury import BankTransaction, BankReconciliation, BankAccount
from finance.models.entries import AccountingEntryLine


class BankReconciliationService:
    """Service de rapprochement bancaire"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def suggest_matches(
        self,
        bank_transaction_id: int,
        max_days_gap: int = 15,
        tolerance: float = 0.01,
    ) -> List[Dict]:
        """
        Suggère des correspondances pour une transaction bancaire
        
        Args:
            bank_transaction_id : ID de la transaction
            max_days_gap : Écart maximal en jours
            tolerance : Tolérance sur le montant
            
        Returns:
            List[Dict] : Suggestions d'écritures
        """
        transaction = self.db.query(BankTransaction).get(bank_transaction_id)
        if not transaction:
            return []
        
        # Rechercher des lignes d'écritures correspondantes
        amount = abs(transaction.amount)
        min_date = transaction.transaction_date
        max_date = transaction.transaction_date
        
        suggestions = self.db.query(AccountingEntryLine).join(
            AccountingEntry
        ).filter(
            AccountingEntryLine.account_number.like('5%'),  # Comptes bancaires
            AccountingEntry.dossier_id == transaction.dossier_id,
            AccountingEntry.entry_date >= min_date,
            AccountingEntry.entry_date <= max_date,
            AccountingEntry.status == 'posted',
        ).all()
        
        matches = []
        for line in suggestions:
            line_amount = float(line.debit or line.credit)
            if abs(line_amount - amount) <= tolerance:
                matches.append({
                    'line_id': line.id,
                    'account_number': line.account_number,
                    'amount': line_amount,
                    'entry_date': line.entry.entry_date.isoformat(),
                    'label': line.label or line.entry.label,
                    'match_score': self._calculate_match_score(transaction, line),
                })
        
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches[:10]

    def _calculate_match_score(self, transaction: BankTransaction, line: AccountingEntryLine) -> float:
        """Calcule un score de correspondance"""
        score = 0.0
        
        # Score par montant (50 points max)
        amount_diff = abs(abs(float(transaction.amount)) - float(line.debit or line.credit))
        score += max(0, 50 - amount_diff * 100)
        
        # Score par date (30 points max)
        # À implémenter
        
        # Score par similarité de libellé (20 points max)
        # À implémenter
        
        return score

    def reconcile(
        self,
        bank_transaction_id: int,
        entry_line_ids: List[int],
    ) -> bool:
        """
        Rapproche une transaction bancaire avec des lignes d'écritures
        
        Args:
            bank_transaction_id : ID de la transaction
            entry_line_ids : IDs des lignes d'écritures
        """
        transaction = self.db.query(BankTransaction).get(bank_transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {bank_transaction_id} inexistante")
        
        lines = self.db.query(AccountingEntryLine).filter(
            AccountingEntryLine.id.in_(entry_line_ids)
        ).all()
        
        # Vérifier que les montants correspondent
        transaction_amount = abs(transaction.amount)
        lines_amount = sum(float(l.debit or l.credit) for l in lines)
        
        if abs(transaction_amount - lines_amount) > 0.01:
            raise ValueError(
                f"Incohérence de montant : Transaction={transaction_amount}, "
                f"Lignes={lines_amount}"
            )
        
        # Marquer comme rapproché
        transaction.is_reconciled = True
        transaction.matched_entry_line_ids = ','.join(map(str, entry_line_ids))
        
        for line in lines:
            line.is_reconciled = True
        
        self.db.commit()
        return True

    def create_reconciliation(
        self,
        bank_account_id: int,
        dossier_id: int,
        period_start: date,
        period_end: date,
        start_balance: Decimal,
        end_balance: Decimal,
        statement_number: Optional[str] = None,
    ) -> BankReconciliation:
        """Crée un nouveau rapprochement bancaire"""
        reconciliation = BankReconciliation(
            bank_account_id=bank_account_id,
            dossier_id=dossier_id,
            period_start=period_start,
            period_end=period_end,
            start_balance=start_balance,
            end_balance=end_balance,
            statement_number=statement_number,
            status='in_progress',
        )
        
        self.db.add(reconciliation)
        self.db.commit()
        self.db.refresh(reconciliation)
        
        return reconciliation

    def complete_reconciliation(
        self,
        reconciliation_id: int,
        reconciled_by: Optional[str] = None,
    ) -> BankReconciliation:
        """Termine un rapprochement"""
        reconciliation = self.db.query(BankReconciliation).get(reconciliation_id)
        if not reconciliation:
            raise ValueError(f"Rapprochement {reconciliation_id} inexistant")
        
        reconciliation.status = 'completed'
        reconciliation.is_completed = True
        reconciliation.reconciled_by = reconciled_by
        
        from datetime import datetime
        reconciliation.reconciled_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(reconciliation)
        
        return reconciliation
