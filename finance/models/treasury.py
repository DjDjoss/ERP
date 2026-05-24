# -*- coding: utf-8 -*-
"""
Modèles de trésorerie et rapprochement bancaire

- BankAccount : Compte bancaire
- BankTransaction : Transaction bancaire (relevé)
- BankReconciliation : Rapprochement bancaire
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from core.db_postgresql import Base


class BankAccount(Base):
    """
    Compte bancaire
    
    Représente un compte bancaire de l'entreprise.
    Lié à un compte comptable (classe 512).
    
    Attributs :
        - account_number : Numéro de compte bancaire (IBAN)
        - bank_code : Code banque
        - branch_code : Code guichet
        - rib_key : Clé RIB
        - currency : Devise (EUR par défaut)
        - is_active : Actif/inactif
    """
    __tablename__ = "finance_bank_accounts"
    __table_args__ = (
        UniqueConstraint("dossier_id", "account_number", name="uq_finance_bank_account_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    
    # Informations bancaires
    account_number = Column(String(34), nullable=False)  # IBAN
    bank_code = Column(String(10), nullable=True)  # Code banque
    branch_code = Column(String(10), nullable=True)  # Code guichet
    rib_key = Column(String(2), nullable=True)  # Clé RIB
    bic_swift = Column(String(11), nullable=True)  # BIC/SWIFT
    
    # Comptabilité
    accounting_account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=True, index=True)
    currency = Column(String(3), nullable=False, default="EUR")
    
    # Statut
    label = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Soldes
    last_statement_balance = Column(Numeric(14, 2), nullable=True)  # Solde dernier relevé
    last_statement_date = Column(Date, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relations
    accounting_account = relationship("AccountingAccount", backref="bank_accounts")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")
    reconciliations = relationship("BankReconciliation", back_populates="bank_account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<BankAccount(id={self.id}, number='{self.account_number}', label='{self.label}')>"

    @property
    def iban_formatted(self) -> str:
        """Retourne l'IBAN formaté avec espaces"""
        if not self.account_number:
            return ""
        # Format français : 5 caractères par groupe
        iban = self.account_number.replace(" ", "")
        return " ".join(iban[i:i+5] for i in range(0, len(iban), 5))


class BankTransaction(Base):
    """
    Transaction bancaire (ligne de relevé)
    
    Importée depuis le relevé bancaire (CSV, EDI, etc.)
    Peut être rapprochée avec une ou plusieurs écritures comptables.
    
    Attributs :
        - transaction_date : Date de valeur
        - value_date : Date d'opération
        - amount : Montant (positif=débit pour la banque, négatif=crédit)
        - counterparty : Contrepartie (nom du tiers)
        - reference : Référence bancaire
        - is_reconciled : Est rapprochée
    """
    __tablename__ = "finance_bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("finance_bank_accounts.id"), nullable=False, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    
    # Dates
    transaction_date = Column(Date, nullable=False)  # Date de valeur
    value_date = Column(Date, nullable=True)  # Date d'opération
    booking_date = Column(Date, nullable=True)  # Date de comptabilisation
    
    # Montants
    amount = Column(Numeric(14, 2), nullable=False)  # Positif = débit, Négatif = crédit
    balance_after = Column(Numeric(14, 2), nullable=True)  # Solde après transaction
    
    # Informations
    label = Column(String(500), nullable=False)
    counterparty_name = Column(String(200), nullable=True)
    counterparty_iban = Column(String(34), nullable=True)
    reference = Column(String(100), nullable=True)  # Référence bancaire
    additional_info = Column(String(500), nullable=True)
    
    # Rapprochement
    is_reconciled = Column(Boolean, nullable=False, default=False)
    reconciliation_id = Column(Integer, ForeignKey("finance_bank_reconciliations.id"), nullable=True)
    
    # Correspondance comptable
    suggested_account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=True)
    matched_entry_line_ids = Column(String(500), nullable=True)  # IDs des lignes d'écritures appariées (JSON-like)
    
    # Origine
    import_source = Column(String(50), nullable=True)  # CSV, EDI, API, manual
    import_batch_id = Column(String(100), nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relations
    bank_account = relationship("BankAccount", back_populates="transactions")
    suggested_account = relationship("AccountingAccount", backref="suggested_transactions")

    def __repr__(self):
        return f"<BankTransaction(id={self.id}, date='{self.transaction_date}', amount={self.amount})>"

    @property
    def is_debit(self) -> bool:
        """Vérifie si c'est un débit (sortie d'argent)"""
        return self.amount > 0

    @property
    def is_credit(self) -> bool:
        """Vérifie si c'est un crédit (entrée d'argent)"""
        return self.amount < 0

    @property
    def absolute_amount(self) -> Decimal:
        """Retourne la valeur absolue du montant"""
        return abs(self.amount)


class BankReconciliation(Base):
    """
    Rapprochement bancaire
    
    Enregistrement qui lie des transactions bancaires
    à des écritures comptables.
    
    Attributs :
        - statement_date : Date du relevé
        - statement_number : Numéro du relevé
        - start_balance : Solde initial
        - end_balance : Solde final
        - is_completed : Rapprochement terminé
    """
    __tablename__ = "finance_bank_reconciliations"

    id = Column(Integer, primary_key=True, index=True)
    bank_account_id = Column(Integer, ForeignKey("finance_bank_accounts.id"), nullable=False, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    
    # Identification
    statement_number = Column(String(50), nullable=True)
    statement_date = Column(Date, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Soldes
    start_balance = Column(Numeric(14, 2), nullable=False)  # Solde début de période
    end_balance = Column(Numeric(14, 2), nullable=False)   # Solde fin de période
    reconciled_balance = Column(Numeric(14, 2), nullable=True)  # Solde rapproché
    
    # Statistiques
    total_transactions = Column(Integer, nullable=False, default=0)
    total_reconciled_transactions = Column(Integer, nullable=False, default=0)
    total_unreconciled_transactions = Column(Integer, nullable=False, default=0)
    difference = Column(Numeric(14, 2), nullable=True)  # Écart de rapprochement
    
    # Statut
    status = Column(String(20), nullable=False, default="in_progress")  # in_progress, completed, locked
    is_completed = Column(Boolean, nullable=False, default=False)
    is_locked = Column(Boolean, nullable=False, default=False)
    
    # Audit
    reconciled_by = Column(String(100), nullable=True)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relations
    bank_account = relationship("BankAccount", back_populates="reconciliations")
    entry_lines = relationship(
        "AccountingEntryLine",
        back_populates="bank_reconciliation",
    )

    def __repr__(self):
        return f"<BankReconciliation(id={self.id}, statement='{self.statement_number}', status='{self.status}')>"

    @property
    def reconciliation_rate(self) -> float:
        """Retourne le taux de rapprochement en %"""
        if self.total_transactions == 0:
            return 0.0
        return (self.total_reconciled_transactions / self.total_transactions) * 100

    def update_statistics(self):
        """Met à jour les statistiques de rapprochement"""
        # Sera implémenté dans le service de rapprochement
        pass
