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
    func,
)
from sqlalchemy.orm import relationship

from backend.connection_manager import Base


class AccountingFiscalYear(Base):
    __tablename__ = "accounting_fiscal_years"
    __table_args__ = (
        UniqueConstraint("dossier_id", "label", name="uq_accounting_fiscal_year_label"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    label = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="open")


class AccountingJournal(Base):
    __tablename__ = "accounting_journals"
    __table_args__ = (
        UniqueConstraint("dossier_id", "code", name="uq_accounting_journal_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    code = Column(String, nullable=False)
    label = Column(String, nullable=False)
    journal_type = Column(String, nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)


class AccountingAccount(Base):
    __tablename__ = "accounting_accounts"
    __table_args__ = (
        UniqueConstraint("dossier_id", "number", name="uq_accounting_account_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    number = Column(String, nullable=False, index=True)
    label = Column(String, nullable=False)
    account_class = Column(String)
    account_type = Column(String, nullable=False, default="general")
    is_active = Column(Boolean, nullable=False, default=True)


class AccountingEntry(Base):
    __tablename__ = "accounting_entries"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    fiscal_year_id = Column(Integer, ForeignKey("accounting_fiscal_years.id"), nullable=False)
    journal_id = Column(Integer, ForeignKey("accounting_journals.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    document_date = Column(Date)
    piece_number = Column(String)
    label = Column(String, nullable=False)
    source = Column(String, nullable=False, default="manual")
    status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lines = relationship(
        "AccountingEntryLine",
        cascade="all, delete-orphan",
        back_populates="entry",
    )


class AccountingEntryLine(Base):
    __tablename__ = "accounting_entry_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("accounting_entries.id"), nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("accounting_accounts.id"))
    account_number = Column(String, nullable=False, index=True)
    third_party = Column(String)
    label = Column(String)
    debit = Column(Numeric(14, 2), nullable=False, default=0)
    credit = Column(Numeric(14, 2), nullable=False, default=0)
    vat_code = Column(String)

    entry = relationship("AccountingEntry", back_populates="lines")


class AccountingAuditLog(Base):
    __tablename__ = "accounting_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String)
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ElectronicInvoice(Base):
    __tablename__ = "electronic_invoices"
    __table_args__ = (
        UniqueConstraint("dossier_id", "invoice_number", name="uq_einvoice_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    invoice_number = Column(String, nullable=False)
    partner_name = Column(String, nullable=False)
    partner_siret = Column(String)
    direction = Column(String, nullable=False, default="outgoing")
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date)
    tax_excluded_amount = Column(Numeric(14, 2), nullable=False, default=0)
    vat_amount = Column(Numeric(14, 2), nullable=False, default=0)
    tax_included_amount = Column(Numeric(14, 2), nullable=False, default=0)
    format = Column(String, nullable=False, default="factur-x")
    platform_status = Column(String, nullable=False, default="draft")
    lifecycle_status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(Integer, primary_key=True, index=True)
    dossier_id = Column(Integer, ForeignKey("dossiers.id"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False)
    label = Column(String, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False, default=0)
    bank_account = Column(String)
    matched_entry_id = Column(Integer, ForeignKey("accounting_entries.id"))
    reconciliation_status = Column(String, nullable=False, default="unmatched")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
