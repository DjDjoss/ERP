from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AccountingFeatureCatalog(BaseModel):
    source: str
    title: str
    items: list[str]


class AccountingSetupStatus(BaseModel):
    dossier_id: int
    fiscal_years: int
    journals: int
    accounts: int
    entries: int
    ready: bool


class FiscalYear(BaseModel):
    id: int
    dossier_id: int
    label: str
    start_date: date
    end_date: date
    status: str

    model_config = ConfigDict(from_attributes=True)


class JournalBase(BaseModel):
    code: str
    label: str
    journal_type: str = "general"
    is_active: bool = True

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value):
        return str(value or "").strip().upper()


class JournalCreate(JournalBase):
    pass


class Journal(JournalBase):
    id: int
    dossier_id: int

    model_config = ConfigDict(from_attributes=True)


class AccountBase(BaseModel):
    number: str
    label: str
    account_class: str | None = None
    account_type: str = "general"
    is_active: bool = True

    @field_validator("number", mode="before")
    @classmethod
    def normalize_number(cls, value):
        return str(value or "").strip()


class AccountCreate(AccountBase):
    pass


class Account(AccountBase):
    id: int
    dossier_id: int

    model_config = ConfigDict(from_attributes=True)


class EntryLineCreate(BaseModel):
    account_number: str
    third_party: str | None = None
    label: str | None = None
    debit: Decimal = Decimal("0.00")
    credit: Decimal = Decimal("0.00")
    vat_code: str | None = None

    @field_validator("account_number", mode="before")
    @classmethod
    def normalize_account_number(cls, value):
        return str(value or "").strip()


class EntryCreate(BaseModel):
    fiscal_year_id: int
    journal_id: int
    entry_date: date
    document_date: date | None = None
    piece_number: str | None = None
    label: str
    source: str = "manual"
    status: str = "draft"
    lines: list[EntryLineCreate]


class EntryLine(BaseModel):
    id: int
    account_number: str
    third_party: str | None = None
    label: str | None = None
    debit: Decimal
    credit: Decimal
    vat_code: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Entry(BaseModel):
    id: int
    dossier_id: int
    fiscal_year_id: int
    journal_id: int
    entry_date: date
    document_date: date | None = None
    piece_number: str | None = None
    label: str
    source: str
    status: str
    created_at: datetime
    lines: list[EntryLine] = []

    model_config = ConfigDict(from_attributes=True)


class TrialBalanceRow(BaseModel):
    account_number: str
    account_label: str
    debit: Decimal
    credit: Decimal
    balance: Decimal


class LedgerLine(BaseModel):
    entry_id: int
    entry_date: date
    journal_code: str
    piece_number: str | None = None
    account_number: str
    account_label: str
    label: str
    debit: Decimal
    credit: Decimal
    balance: Decimal


# === NOUVEAUX SCHEMAS POUR ETATS FINANCIERS ===

class BalanceSheetItem(BaseModel):
    """Element du bilan"""
    account_number: str
    account_label: str
    debit_total: Decimal
    credit_total: Decimal
    net_amount: Decimal
    category: str  # asset, liability, equity


class BalanceSheetSummary(BaseModel):
    """Resume du bilan"""
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
    net_income: Decimal
    balance_check: bool  # True si Actif = Passif + Capitaux propres


class IncomeStatementItem(BaseModel):
    """Element du compte de resultat"""
    account_number: str
    account_label: str
    debit_total: Decimal
    credit_total: Decimal
    net_amount: Decimal
    category: str  # revenue, expense


class IncomeStatementSummary(BaseModel):
    """Resume du compte de resultat"""
    total_revenues: Decimal
    total_expenses: Decimal
    gross_profit: Decimal
    operating_result: Decimal
    net_result: Decimal


class CashFlowItem(BaseModel):
    """Element du tableau de flux de tresorerie"""
    description: str
    amount: Decimal
    category: str  # operating, investing, financing


class CashFlowSummary(BaseModel):
    """Resume des flux de tresorerie"""
    operating_cash_flow: Decimal
    investing_cash_flow: Decimal
    financing_cash_flow: Decimal
    net_cash_change: Decimal
    opening_balance: Decimal
    closing_balance: Decimal


class DashboardKPI(BaseModel):
    """Indicateur de performance pour tableau de bord"""
    name: str
    value: Decimal
    unit: str
    trend: str | None = None  # up, down, stable
    previous_value: Decimal | None = None


class FinancialDashboard(BaseModel):
    """Tableau de bord financier complet"""
    dossier_id: int
    period_start: date
    period_end: date
    kpis: list[DashboardKPI]
    balance_summary: BalanceSheetSummary | None = None
    income_summary: IncomeStatementSummary | None = None
    cash_flow_summary: CashFlowSummary | None = None


class ExportOptions(BaseModel):
    """Options d'export"""
    format: str = "pdf"  # pdf, excel, csv
    include_details: bool = True
    currency: str = "EUR"
    language: str = "fr"


class InvoiceBase(BaseModel):
    invoice_number: str
    partner_name: str
    partner_siret: str | None = None
    direction: str = "outgoing"
    issue_date: date
    due_date: date | None = None
    tax_excluded_amount: Decimal = Decimal("0.00")
    vat_amount: Decimal = Decimal("0.00")
    tax_included_amount: Decimal = Decimal("0.00")
    format: str = "factur-x"
    platform_status: str = "draft"
    lifecycle_status: str = "draft"


class InvoiceCreate(InvoiceBase):
    pass


class Invoice(InvoiceBase):
    id: int
    dossier_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BankTransactionBase(BaseModel):
    transaction_date: date
    label: str
    amount: Decimal = Decimal("0.00")
    bank_account: str | None = None
    matched_entry_id: int | None = None
    reconciliation_status: str = "unmatched"


class BankTransactionCreate(BankTransactionBase):
    pass


class BankTransaction(BankTransactionBase):
    id: int
    dossier_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLog(BaseModel):
    id: int
    dossier_id: int
    action: str
    entity_type: str
    entity_id: str | None = None
    details: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VatSummary(BaseModel):
    collected_vat: Decimal
    deductible_vat: Decimal
    net_vat_due: Decimal


class AccountingControlIssue(BaseModel):
    severity: str
    code: str
    message: str
    count: int = 0


class Accounting2026Status(BaseModel):
    dossier_id: int
    setup: AccountingSetupStatus
    invoices: int
    invoices_pending_platform: int
    bank_transactions: int
    bank_unmatched: int
    audit_events: int
    vat: VatSummary
    controls: list[AccountingControlIssue]
