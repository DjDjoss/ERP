# -*- coding: utf-8 -*-
"""
Modèles pour les états financiers et rapports

- TrialBalance : Balance comptable (snapshot)
- GeneralLedger : Grand Livre (snapshot)

Ces modèles permettent de stocker des snapshots
des états financiers à une date donnée.
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from core.db_postgresql import Base


class TrialBalance(Base):
    """
    Balance comptable (snapshot)
    
    Capture l'état des soldes de tous les comptes
    à une date donnée. Permet de comparer les balances
    dans le temps sans recalculer.
    
    Attributs :
        - period_start : Date de début de période
        - period_end : Date de fin de période
        - account_number : Numéro du compte
        - opening_debit/credit : Soldes d'ouverture
        - period_debit/credit : Mouvements de la période
        - closing_debit/credit : Soldes de clôture
    """
    __tablename__ = "finance_trial_balances"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("finance_fiscal_years.id"), nullable=False, index=True)
    
    # Période
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Compte
    account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=False, index=True)
    account_number = Column(String(20), nullable=False, index=True)
    account_label = Column(String(200), nullable=False)
    
    # Soldes d'ouverture
    opening_debit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    opening_credit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Mouvements de la période
    period_debit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    period_credit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Soldes de clôture
    closing_debit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    closing_credit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Nombre d'écritures
    entry_count = Column(Integer, nullable=False, default=0)
    
    # Audit
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    generated_by = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<TrialBalance(account='{self.account_number}', period='{self.period_end}')>"

    @property
    def opening_balance(self) -> Decimal:
        """Retourne le solde d'ouverture (net)"""
        return self.opening_debit - self.opening_credit

    @property
    def period_balance(self) -> Decimal:
        """Retourne le mouvement de la période (net)"""
        return self.period_debit - self.period_credit

    @property
    def closing_balance(self) -> Decimal:
        """Retourne le solde de clôture (net)"""
        return self.closing_debit - self.closing_credit

    @property
    def balance_type(self) -> str:
        """Retourne le type de solde (debitor/creditor/null)"""
        if self.closing_debit > self.closing_credit:
            return "debitor"
        elif self.closing_credit > self.closing_debit:
            return "creditor"
        return "null"


class GeneralLedger(Base):
    """
    Grand Livre (snapshot)
    
    Enregistrement détaillé de toutes les écritures
    pour un compte donné sur une période.
    Utile pour générer rapidement le grand livre
    sans requêter toutes les écritures à chaque fois.
    
    Note : Ce modèle est optionnel et peut être généré
    à la volée depuis les écritures. Il est utile pour
    les performances sur les gros volumes.
    """
    __tablename__ = "finance_general_ledger"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("finance_fiscal_years.id"), nullable=False, index=True)
    
    # Référence à l'écriture originale
    entry_id = Column(Integer, ForeignKey("finance_entries.id"), nullable=False, index=True)
    entry_line_id = Column(Integer, ForeignKey("finance_entry_lines.id"), nullable=False, unique=True, index=True)
    
    # Période
    entry_date = Column(Date, nullable=False, index=True)
    period_date = Column(Date, nullable=True)
    
    # Compte
    account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=False, index=True)
    account_number = Column(String(20), nullable=False, index=True)
    account_label = Column(String(200), nullable=False)
    
    # Journal
    journal_id = Column(Integer, ForeignKey("finance_journals.id"), nullable=False)
    journal_code = Column(String(10), nullable=False)
    
    # Identification
    entry_number = Column(Integer, nullable=False)
    piece_number = Column(String(50), nullable=True)
    line_number = Column(Integer, nullable=False)
    
    # Montants
    debit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    credit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Tiers
    third_party_code = Column(String(50), nullable=True, index=True)
    third_party_name = Column(String(200), nullable=True)
    
    # Lettrage
    lettering_code = Column(String(50), nullable=True, index=True)
    
    # Libellé
    label = Column(String(500), nullable=False)
    
    # Solde cumulé (calculé lors de la génération)
    cumulative_debit = Column(Numeric(14, 2), nullable=True)
    cumulative_credit = Column(Numeric(14, 2), nullable=True)
    cumulative_balance = Column(Numeric(14, 2), nullable=True)
    
    # Audit
    generated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<GeneralLedger(entry={self.entry_number}, account='{self.account_number}', debit={self.debit}, credit={self.credit})>"
