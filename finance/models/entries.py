# -*- coding: utf-8 -*-
"""
Modèles d'écritures comptables

- AccountingEntry : Écriture comptable (pièce maîtresse)
- AccountingEntryLine : Ligne d'écriture (débit/crédit)

Règle fondamentale : Partie double
Toute écriture doit avoir Total Débit = Total Crédit
"""

from datetime import date, datetime
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
    Text,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from core.db_postgresql import Base


class AccountingEntry(Base):
    """
    Écriture comptable
    
    Une écriture est composée de plusieurs lignes (au minimum 2).
    Elle doit toujours être équilibrée (débit = crédit).
    
    Statuts :
        - draft : Brouillon (modifiable)
        - posted : Validée/comptabilisée (non modifiable, seulement annulation)
        - cancelled : Annulée
        - review : En révision
    
    Attributs :
        - entry_number : Numéro séquentiel unique dans le journal
        - piece_number : Numéro de pièce justificative
        - source : Origine (manual, invoice, payment, etc.)
    """
    __tablename__ = "finance_entries"
    __table_args__ = (
        UniqueConstraint("journal_id", "entry_number", name="uq_finance_entry_journal_number"),
    )

    STATUS_CHOICES = {
        "draft": "Brouillon",
        "posted": "Validée",
        "cancelled": "Annulée",
        "review": "En révision",
    }

    SOURCE_CHOICES = [
        "manual",       # Saisie manuelle
        "invoice",      # Facture client/fournisseur
        "payment",      # Paiement
        "salary",       # Paie
        "inventory",    # Inventaire
        "asset",        # Immobilisation
        "tax",          # Déclaration TVA
        "closing",      # Clôture
        "opening",      # Ouverture
    ]

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("finance_fiscal_years.id"), nullable=False, index=True)
    journal_id = Column(Integer, ForeignKey("finance_journals.id"), nullable=False, index=True)
    
    # Identification
    entry_number = Column(Integer, nullable=False)  # Numéro dans le journal
    piece_number = Column(String(50), nullable=True)  # Pièce justificative
    label = Column(String(500), nullable=False)  # Libellé général
    
    # Dates
    entry_date = Column(Date, nullable=False, index=True)  # Date d'écriture
    document_date = Column(Date, nullable=True)  # Date de pièce
    period_date = Column(Date, nullable=True)  # Date de période (pour lettrage)
    
    # Métadonnées
    source = Column(String(30), nullable=False, default="manual")
    source_id = Column(Integer, nullable=True)  # ID dans la table source (ex: facture_id)
    status = Column(String(20), nullable=False, default="draft")
    is_system = Column(Boolean, nullable=False, default=False)  # Générée automatiquement
    
    # Totaux (calculés mais stockés pour performance)
    total_debit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_credit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # Audit
    created_by = Column(String(100), nullable=True)
    validated_by = Column(String(100), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relations
    fiscal_year = relationship("FiscalYear", back_populates="entries")
    journal = relationship("AccountingJournal", back_populates="entries")
    lines = relationship(
        "AccountingEntryLine",
        back_populates="entry",
        cascade="all, delete-orphan",
        order_by="AccountingEntryLine.line_number",
    )

    def __repr__(self):
        return f"<AccountingEntry(id={self.id}, number='{self.entry_number}', status='{self.status}')>"

    @property
    def is_balanced(self) -> bool:
        """Vérifie si l'écriture est équilibrée"""
        return self.total_debit == self.total_credit

    @property
    def balance_difference(self) -> Decimal:
        """Retourne la différence débit-crédit"""
        return abs(self.total_debit - self.total_credit)

    @property
    def is_posted(self) -> bool:
        """Vérifie si l'écriture est validée"""
        return self.status == "posted"

    @property
    def is_draft(self) -> bool:
        """Vérifie si l'écriture est en brouillon"""
        return self.status == "draft"

    @property
    def is_cancelled(self) -> bool:
        """Vérifie si l'écriture est annulée"""
        return self.status == "cancelled"

    def recalculate_totals(self):
        """Recalcule les totaux débit et crédit depuis les lignes"""
        self.total_debit = sum(line.debit or Decimal("0.00") for line in self.lines)
        self.total_credit = sum(line.credit or Decimal("0.00") for line in self.lines)

    def validate_balance(self) -> bool:
        """
        Valide que l'écriture est équilibrée.
        Lève une exception si déséquilibrée.
        """
        if not self.is_balanced:
            raise ValueError(
                f"Écriture déséquilibrée : Débit={self.total_debit} ≠ Crédit={self.total_credit}"
            )
        return True


class AccountingEntryLine(Base):
    """
    Ligne d'écriture comptable
    
    Chaque ligne représente un mouvement sur un compte :
    - Soit au débit
    - Soit au crédit
    - Jamais les deux simultanément
    
    Attributs :
        - line_number : Ordre dans l'écriture
        - account_id : Compte concerné
        - debit : Montant au débit
        - credit : Montant au crédit
        - third_party_code : Code tiers pour rapprochement
        - vat_amount : Montant TVA (si applicable)
        - lettering_code : Code de lettrage
    """
    __tablename__ = "finance_entry_lines"
    __table_args__ = (
        CheckConstraint("debit >= 0", name="chk_finance_line_debit_positive"),
        CheckConstraint("credit >= 0", name="chk_finance_line_credit_positive"),
        CheckConstraint(
            "(debit = 0 AND credit > 0) OR (debit > 0 AND credit = 0) OR (debit = 0 AND credit = 0)",
            name="chk_finance_line_debit_xor_credit"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("finance_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False, default=1)
    
    # Compte
    account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=False, index=True)
    account_number = Column(String(20), nullable=False)  # Copie pour historique
    account_label = Column(String(200), nullable=True)  # Copie pour historique
    
    # Tiers (optionnel, pour comptes 4xx)
    third_party_code = Column(String(50), nullable=True, index=True)
    third_party_name = Column(String(200), nullable=True)
    
    # Montants
    debit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    credit = Column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    
    # TVA
    vat_code = Column(String(20), nullable=True)
    vat_rate = Column(Numeric(5, 2), nullable=True)
    vat_amount = Column(Numeric(14, 2), nullable=True)
    
    # Lettrage
    lettering_code = Column(String(50), nullable=True, index=True)
    lettering_date = Column(Date, nullable=True)
    
    # Analytique (pour plus tard)
    analytic_axis = Column(String(50), nullable=True)
    analytic_section = Column(String(50), nullable=True)
    
    # Description
    label = Column(String(500), nullable=True)
    
    # Réconciliation bancaire
    bank_reconciliation_id = Column(Integer, ForeignKey("finance_bank_reconciliations.id"), nullable=True)
    is_reconciled = Column(Boolean, nullable=False, default=False)

    # Relations
    entry = relationship("AccountingEntry", back_populates="lines")
    account = relationship("AccountingAccount", backref="entry_lines")
    bank_reconciliation = relationship("BankReconciliation", back_populates="entry_lines")

    def __repr__(self):
        return f"<AccountingEntryLine(id={self.id}, account='{self.account_number}', debit={self.debit}, credit={self.credit})>"

    @property
    def amount(self) -> Decimal:
        """Retourne le montant (débit ou crédit)"""
        return self.debit if self.debit > 0 else self.credit

    @property
    def direction(self) -> str:
        """Retourne la direction (debit/credit/none)"""
        if self.debit > 0:
            return "debit"
        elif self.credit > 0:
            return "credit"
        return "none"

    def is_third_party_line(self) -> bool:
        """Vérifie si c'est une ligne de tiers (lettrable)"""
        return bool(self.third_party_code) and self.account_number.startswith("4")

    def can_be_lettered(self) -> bool:
        """Vérifie si la ligne peut être lettrée"""
        return self.is_third_party_line() and not self.is_reconciled
