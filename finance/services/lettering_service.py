# -*- coding: utf-8 -*-
"""
Service de lettrage automatique

Permet de lettrer automatiquement les écritures clients/fournisseurs
selon différentes méthodes :
- Par montant et date
- Par référence (facture/paiement)
- Par échéance
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from finance.models.entries import AccountingEntryLine, AccountingEntry
from finance.models.core import AccountingAccount


class LetteringService:
    """Service de lettrage automatique des tiers"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def auto_letter(
        self,
        dossier_id: int,
        account_number: str,
        third_party_code: Optional[str] = None,
        max_days_gap: int = 90,
    ) -> Dict:
        """
        Lettrage automatique pour un compte tiers
        
        Args:
            dossier_id : ID du dossier
            account_number : Numéro de compte (411xxx ou 401xxx)
            third_party_code : Code tiers spécifique (optionnel)
            max_days_gap : Écart maximal en jours entre débit et crédit
            
        Returns:
            Dict : Statistiques de lettrage
        """
        account = self.db.query(AccountingAccount).filter(
            AccountingAccount.dossier_id == dossier_id,
            AccountingAccount.number == account_number,
        ).first()
        
        if not account:
            return {"lettered": 0, "groups": 0}
        
        # Récupérer les lignes non lettrées
        query = self.db.query(AccountingEntryLine).join(
            AccountingEntry
        ).filter(
            AccountingEntryLine.account_id == account.id,
            AccountingEntry.dossier_id == dossier_id,
            AccountingEntry.status == 'posted',
            AccountingEntryLine.lettering_code.is_(None),
        )
        
        if third_party_code:
            query = query.filter(AccountingEntryLine.third_party_code == third_party_code)
        
        lines = query.all()
        
        debits = [l for l in lines if l.debit > 0]
        credits = [l for l in lines if l.credit > 0]
        
        stats = {"lettered": 0, "groups": 0, "suggestions": []}
        
        # Trier par date
        debits.sort(key=lambda x: x.entry.entry_date or date.min)
        credits.sort(key=lambda x: x.entry.entry_date or date.min)
        
        # Lettrer par montants identiques
        for debit in debits:
            if debit.lettering_code:
                continue
                
            for credit in credits:
                if credit.lettering_code:
                    continue
                
                # Vérifier si montants égaux
                if abs(debit.debit - credit.credit) < Decimal('0.01'):
                    # Vérifier écart de date
                    date_diff = abs((credit.entry.entry_date - debit.entry.entry_date).days)
                    if date_diff <= max_days_gap:
                        # Lettrer
                        lettering_code = self._generate_lettering_code()
                        self._apply_lettering([debit.id, credit.id], lettering_code)
                        stats["lettered"] += 2
                        stats["groups"] += 1
        
        return stats

    def _generate_lettering_code(self) -> str:
        """Génère un code de lettrage unique"""
        import uuid
        return f"L{uuid.uuid4().hex[:8].upper()}"

    def _apply_lettering(self, line_ids: List[int], lettering_code: str):
        """Applique le code de lettrage à des lignes"""
        today = date.today()
        for line_id in line_ids:
            line = self.db.query(AccountingEntryLine).get(line_id)
            if line:
                line.lettering_code = lettering_code
                line.lettering_date = today
        self.db.commit()

    def get_unlettered_lines(
        self,
        dossier_id: int,
        account_class: str = '4',
        older_than_days: int = 30,
    ) -> List[Dict]:
        """
        Retourne les lignes non lettrées anciennes
        
        Args:
            dossier_id : ID du dossier
            account_class : Classe de comptes ('4' pour tiers)
            older_than_days : Ancienneté minimale en jours
        """
        cutoff_date = date.today() - timedelta(days=older_than_days)
        
        lines = self.db.query(AccountingEntryLine).join(
            AccountingEntry
        ).join(
            AccountingAccount
        ).filter(
            AccountingEntry.dossier_id == dossier_id,
            AccountingAccount.account_class == account_class,
            AccountingEntryLine.lettering_code.is_(None),
            AccountingEntry.status == 'posted',
            AccountingEntry.entry_date < cutoff_date,
        ).order_by(
            AccountingEntry.entry_date,
        ).all()
        
        return [
            {
                'line_id': line.id,
                'account_number': line.account_number,
                'third_party_code': line.third_party_code,
                'amount': float(line.debit or line.credit),
                'direction': 'debit' if line.debit > 0 else 'credit',
                'entry_date': line.entry.entry_date.isoformat(),
                'label': line.label or line.entry.label,
            }
            for line in lines
        ]

    def manual_letter(
        self,
        line_ids: List[int],
        lettering_code: Optional[str] = None,
    ) -> bool:
        """
        Lettrage manuel de lignes sélectionnées
        
        Args:
            line_ids : IDs des lignes à lettrer
            lettering_code : Code de lettrage (généré si None)
        """
        if not lettering_code:
            lettering_code = self._generate_lettering_code()
        
        # Vérifier que le solde est nul
        lines = self.db.query(AccountingEntryLine).filter(
            AccountingEntryLine.id.in_(line_ids)
        ).all()
        
        total_debit = sum(l.debit or Decimal('0') for l in lines)
        total_credit = sum(l.credit or Decimal('0') for l in lines)
        
        if abs(total_debit - total_credit) > Decimal('0.01'):
            raise ValueError(
                f"Le lettrage est déséquilibré : Débit={total_debit} ≠ Crédit={total_credit}"
            )
        
        self._apply_lettering(line_ids, lettering_code)
        return True
