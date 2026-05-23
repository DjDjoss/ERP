# -*- coding: utf-8 -*-
"""
Modèles de base du module Finance

Ces modèles sont le socle du système comptable :
- FiscalYear : Exercice comptable (période fiscale)
- AccountingJournal : Journaux comptables (AC, VE, BQ, CA, OD, AN)
- AccountingAccount : Plan comptable (PCG français)
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
    Text,
    UniqueConstraint,
    CheckConstraint,
    func,
)
from sqlalchemy.orm import relationship

from backend.connection_manager import Base


class FiscalYear(Base):
    """
    Exercice comptable
    
    Un exercice fiscal couvre une période (généralement 12 mois).
    Il peut être ouvert, fermé ou en cours de clôture.
    
    Attributs :
        - dossier_id : Lien vers le dossier (entreprise)
        - label : Libellé (ex: "Exercice 2025")
        - start_date : Date de début
        - end_date : Date de fin
        - status : Statut (draft, open, closing, closed)
        - is_closing_locked : Verrouillage après clôture
    """
    __tablename__ = "finance_fiscal_years"
    __table_args__ = (
        UniqueConstraint("dossier_id", "label", name="uq_finance_fiscal_year_label"),
        CheckConstraint(
            "end_date >= start_date",
            name="chk_finance_fiscal_year_dates"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    label = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="draft")  # draft, open, closing, closed
    is_closing_locked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    # Relations
    entries = relationship("AccountingEntry", back_populates="fiscal_year", cascade="all, delete-orphan")
    journals = relationship("AccountingJournal", back_populates="fiscal_year", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FiscalYear(id={self.id}, label='{self.label}', status='{self.status}')>"

    def is_open(self) -> bool:
        """Vérifie si l'exercice est ouvert (accepte les écritures)"""
        return self.status in ("open",)

    def is_closed(self) -> bool:
        """Vérifie si l'exercice est clôturé"""
        return self.status == "closed"

    def contains_date(self, check_date: date) -> bool:
        """Vérifie si une date appartient à l'exercice"""
        return self.start_date <= check_date <= self.end_date


class AccountingJournal(Base):
    """
    Journal comptable
    
    Les journaux permettent de classer les écritures par type :
    - AC : Achats
    - VE : Ventes
    - BQ : Banque
    - CA : Caisse
    - OD : Opérations Diverses
    - AN : A-Nouveau (réouverture)
    
    Attributs :
        - code : Code unique (ex: "AC", "VE")
        - label : Libellé complet
        - journal_type : Type (purchase, sale, bank, cash, general, opening)
        - is_active : Actif/inactif
    """
    __tablename__ = "finance_journals"
    __table_args__ = (
        UniqueConstraint("dossier_id", "code", name="uq_finance_journal_code"),
    )

    JOURNAL_TYPES = {
        "purchase": "Achats",
        "sale": "Ventes",
        "bank": "Banque",
        "cash": "Caisse",
        "general": "Opérations diverses",
        "opening": "A-Nouveau",
    }

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("finance_fiscal_years.id"), nullable=True, index=True)
    code = Column(String(10), nullable=False)
    label = Column(String(200), nullable=False)
    journal_type = Column(String(20), nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)
    last_entry_number = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relations
    fiscal_year = relationship("FiscalYear", back_populates="journals")
    entries = relationship("AccountingEntry", back_populates="journal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AccountingJournal(code='{self.code}', label='{self.label}')>"

    def get_next_entry_number(self) -> int:
        """Retourne le prochain numéro d'écriture et incrémente le compteur"""
        self.last_entry_number += 1
        return self.last_entry_number


class AccountingAccount(Base):
    """
    Compte comptable (Plan Comptable Général - PCG)
    
    Structure hiérarchique :
    - Classe 1 : Capitaux
    - Classe 2 : Immobilisations
    - Classe 3 : Stocks
    - Classe 4 : Tiers
    - Classe 5 : Financier
    - Classe 6 : Charges
    - Classe 7 : Produits
    
    Attributs :
        - number : Numéro du compte (ex: "411000")
        - label : Intitulé
        - account_class : Classe (1-7)
        - account_type : Type (general, third_party, bank, cash, etc.)
        - is_third_party : Compte de tiers (client/fournisseur)
        - parent_id : Compte parent pour hiérarchie
    """
    __tablename__ = "finance_accounts"
    __table_args__ = (
        UniqueConstraint("dossier_id", "number", name="uq_finance_account_number"),
    )

    ACCOUNT_CLASSES = {
        "1": "Capitaux",
        "2": "Immobilisations",
        "3": "Stocks",
        "4": "Tiers",
        "5": "Financier",
        "6": "Charges",
        "7": "Produits",
    }

    ACCOUNT_TYPES = [
        "general",
        "third_party_customer",
        "third_party_supplier",
        "bank",
        "cash",
        "tax",
        "social",
        "waiting",
    ]

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    number = Column(String(20), nullable=False, index=True)
    label = Column(String(200), nullable=False)
    account_class = Column(String(1), nullable=True)  # 1-7
    account_type = Column(String(30), nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)
    is_third_party = Column(Boolean, nullable=False, default=False)
    third_party_code = Column(String(50), nullable=True)  # Code client/fournisseur
    parent_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relation récursive pour hiérarchie
    parent = relationship("AccountingAccount", remote_side=[id], backref="children")

    def __repr__(self):
        return f"<AccountingAccount(number='{self.number}', label='{self.label}')>"

    @property
    def is_customer(self) -> bool:
        """Vérifie si c'est un compte client"""
        return self.account_type == "third_party_customer" or (self.number.startswith("411") if self.number else False)

    @property
    def is_supplier(self) -> bool:
        """Vérifie si c'est un compte fournisseur"""
        return self.account_type == "third_party_supplier" or (self.number.startswith("401") if self.number else False)

    @property
    def is_bank(self) -> bool:
        """Vérifie si c'est un compte bancaire"""
        return self.account_type == "bank" or (self.number.startswith("512") if self.number else False)

    @property
    def class_label(self) -> str:
        """Retourne le libellé de la classe"""
        return self.ACCOUNT_CLASSES.get(self.account_class, "")
