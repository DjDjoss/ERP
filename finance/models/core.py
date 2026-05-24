# -*- coding: utf-8 -*-
"""
Modèles de base du module Finance

Ces modèles sont le socle du système comptable :
- FiscalYear : Exercice comptable (période fiscale)
- AccountingJournal : Journaux comptables (AC, VE, BQ, CA, OD, AN)
- AccountingAccount : Plan comptable (PCG français)
- AnalyticAxis/Section : Comptabilité analytique
"""

from datetime import date
from decimal import Decimal
from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, CheckConstraint, func, Index
)
from sqlalchemy.orm import relationship

from core.db_postgresql import Base


class FiscalYear(Base):
    """Exercice comptable - Période fiscale d'un dossier"""
    __tablename__ = "finance_fiscal_years"
    __table_args__ = (
        UniqueConstraint("dossier_id", "label", name="uq_finance_fiscal_year_label"),
        CheckConstraint("end_date >= start_date", name="chk_finance_fiscal_year_dates"),
        Index("idx_fiscal_year_dossier", "dossier_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, nullable=False, index=True)
    label = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, open, closing, closed
    is_closing_locked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relation vers Dossier (définie dynamiquement car Dossier est dans un autre module)
    dossier = relationship(
        "Dossier",
        foreign_keys="[FiscalYear.dossier_id]",
        back_populates="fiscal_years",
        overlaps="journals,accounts"
    )
    journals = relationship("AccountingJournal", back_populates="fiscal_year", cascade="all, delete-orphan")
    entries = relationship("AccountingEntry", back_populates="fiscal_year", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FiscalYear(id={self.id}, label='{self.label}', status='{self.status}')>"

    def is_open(self) -> bool:
        return self.status == "open"

    def is_closed(self) -> bool:
        return self.status == "closed"

    def contains_date(self, check_date: date) -> bool:
        return self.start_date <= check_date <= self.end_date


class AccountingJournal(Base):
    """Journal comptable - Classeur des écritures par type"""
    __tablename__ = "finance_journals"
    __table_args__ = (
        UniqueConstraint("dossier_id", "code", name="uq_finance_journal_code"),
        Index("idx_journal_dossier", "dossier_id"),
    )

    JOURNAL_TYPES = {
        "purchase": "Achats", "sale": "Ventes", "bank": "Banque",
        "cash": "Caisse", "general": "Opérations diverses", "opening": "A-Nouveau",
    }

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("finance_fiscal_years.id"), nullable=True, index=True)
    code = Column(String(10), nullable=False)
    label = Column(String(200), nullable=False)
    journal_type = Column(String(20), nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)
    last_entry_number = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    fiscal_year = relationship("FiscalYear", back_populates="journals")
    entries = relationship("AccountingEntry", back_populates="journal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AccountingJournal(code='{self.code}', label='{self.label}')>"

    def get_next_entry_number(self) -> int:
        self.last_entry_number += 1
        return self.last_entry_number


class AccountingAccount(Base):
    """Compte comptable - Plan Comptable Général (PCG)"""
    __tablename__ = "finance_accounts"
    __table_args__ = (
        UniqueConstraint("dossier_id", "number", name="uq_finance_account_number"),
        Index("idx_account_dossier", "dossier_id"),
        Index("idx_account_number", "number"),
    )

    ACCOUNT_CLASSES = {"1": "Capitaux", "2": "Immobilisations", "3": "Stocks",
                       "4": "Tiers", "5": "Financier", "6": "Charges", "7": "Produits"}

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, nullable=False, index=True)
    number = Column(String(20), nullable=False, index=True)
    label = Column(String(200), nullable=False)
    account_class = Column(String(1), nullable=True)
    account_type = Column(String(30), nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)
    is_third_party = Column(Boolean, nullable=False, default=False)
    third_party_code = Column(String(50), nullable=True)
    parent_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    parent = relationship("AccountingAccount", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<AccountingAccount(number='{self.number}', label='{self.label}')>"

    @property
    def is_customer(self) -> bool:
        return self.account_type == "third_party_customer" or (self.number and self.number.startswith("411"))

    @property
    def is_supplier(self) -> bool:
        return self.account_type == "third_party_supplier" or (self.number and self.number.startswith("401"))

    @property
    def is_bank(self) -> bool:
        return self.account_type == "bank" or (self.number and self.number.startswith("512"))


class AnalyticAxis(Base):
    """Axe analytique - Dimension d'analyse (ex: Département, Projet, Produit)"""
    __tablename__ = "finance_analytic_axes"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, nullable=False, index=True)
    code = Column(String(20), nullable=False)
    label = Column(String(200), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    sections = relationship("AnalyticSection", back_populates="axis", cascade="all, delete-orphan")


class AnalyticSection(Base):
    """Section analytique - Valeur dans un axe (ex: Commercial, IT pour axe Département)"""
    __tablename__ = "finance_analytic_sections"
    __table_args__ = (UniqueConstraint("axis_id", "code", name="uq_analytic_section_code"),)

    id = Column(Integer, primary_key=True, index=True)
    axis_id = Column(Integer, ForeignKey("finance_analytic_axes.id"), nullable=False, index=True)
    code = Column(String(20), nullable=False)
    label = Column(String(200), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    axis = relationship("AnalyticAxis", back_populates="sections")
