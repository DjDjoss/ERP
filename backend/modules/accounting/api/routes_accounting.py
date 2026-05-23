import csv
from datetime import date
from decimal import Decimal
from pathlib import Path
from io import StringIO, BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse, StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from backend.connection_manager import get_db
from backend.events_manager import events_manager
from backend.routes.events import make_event
from backend.modules.accounting import models
from backend.modules.accounting.api import schemas
from backend.modules.dossiers.models import Dossier


router = APIRouter(prefix="/accounting", tags=["Comptabilite"])


DEFAULT_JOURNALS = [
    ("AN", "A nouveau", "opening"),
    ("AC", "Achats", "purchase"),
    ("VE", "Ventes", "sale"),
    ("BQ", "Banque", "bank"),
    ("CA", "CREDIT AGRICOLE", "bank"),
    ("CA", "Caisse", "cash"),
    ("OD", "Operations diverses", "general"),
]

DEFAULT_ACCOUNTS = [
    ("101000", "Capital social", "1", "general"),
    ("120000", "Resultat de l'exercice", "1", "general"),
    ("401000", "Fournisseurs", "4", "third_party"),
    ("411000", "Clients", "4", "third_party"),
    ("445660", "TVA deductible", "4", "vat"),
    ("445710", "TVA collectee", "4", "vat"),
    ("512000", "Banque", "5", "general"),
    ("530000", "Caisse", "5", "general"),
    ("607000", "Achats de marchandises", "6", "expense"),
    ("706000", "Prestations de services", "7", "income"),
    ("707000", "Ventes de marchandises", "7", "income"),
]

PCG_TEXT_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

REFERENCE_FEATURES = [
    "Comptabilite generale avec comptes, journaux, guides de saisie et modeles d'ecritures",
    "Gestion commerciale/facturation avec modeles de documents et rapports",
    "TVA: formulaires CA3/CA12, operations, regimes et historiques",
    "Banque: banques, parametrage d'operations bancaires et rapprochement a construire",
    "Editions: rapports, impressions, PDF, Excel/OpenXML et modele de documents",
    "Referentiels: pays, devises, codes NAF, codes postaux, civilites, modes de reglement",
    "EDI/declarations: modules EDI, DEP/DEB/Intrastat et exports fiscaux visibles",
    "Connecteurs techniques: SQL Server, MySQL, Pervasive, WebClient et lanceur",
]

ERP_2026_FEATURES = [
    "Facturation electronique B2B via plateforme agreee et suivi du cycle de vie",
    "E-reporting des transactions et donnees de paiement",
    "Annuaire de facturation electronique: plateforme de reception et adresse de facturation",
    "Formats Factur-X, UBL/CII et profils normalises de la reforme",
    "PCG 2026 et plan de comptes par dossier",
    "FEC, piste d'audit fiable, journal d'audit et verrouillage des periodes",
    "Lettrage clients/fournisseurs, echeanciers, relances et rapprochement bancaire",
    "Tableaux de bord: tresorerie, TVA, marges, impayes, resultat et controle des anomalies",
    "API-first: automatisations, imports bancaires, OCR facture, connecteurs experts-comptables",
]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _pcg_text_file() -> Path | None:
    root = _project_root()
    candidates = sorted(
        [
            path
            for path in root.glob("PCG*.txt")
            if path.is_file() and "g" in path.stem.lower()
        ],
        key=lambda path: path.name.lower(),
    )
    return candidates[0] if candidates else None


def _read_pcg_text_accounts() -> list[tuple[str, str, str, str]]:
    pcg_file = _pcg_text_file()
    if pcg_file is None:
        return []

    last_error: Exception | None = None
    for encoding in PCG_TEXT_ENCODINGS:
        try:
            with pcg_file.open("r", encoding=encoding, newline="") as handle:
                reader = csv.reader(handle, delimiter="\t")
                accounts = []
                for row in reader:
                    if len(row) < 2:
                        continue

                    number = row[0].strip()
                    label = row[1].strip()
                    raw_type = row[2].strip().lower() if len(row) > 2 else ""

                    if not number.isdigit() or not label:
                        continue

                    account_type = "root" if raw_type.startswith("racine") else "general"
                    account_class = number[0]
                    accounts.append((number, label, account_class, account_type))

                return accounts
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error:
        raise HTTPException(500, f"Lecture du PCG general impossible: {last_error}")
    return []


def _reference_inventory() -> dict:
    root = _project_root()
    reference_dir = next(
        (
            path
            for path in root.iterdir()
            if path.is_dir()
            and (path / "Accounting7.0FRFR30AI").exists()
            and (path / "Invoicing7.0FRFR30AI").exists()
        ),
        root / "reference_compta",
    )
    accounting_data = reference_dir / "Accounting7.0FRFR30AI" / "Data" / "FR"
    invoicing_data = reference_dir / "Invoicing7.0FRFR30AI" / "Data" / "FR"

    accounting_references = {
        "plan de comptes": "PCGAccounts.xml",
        "comptes auxiliaires et generaux": "Accounts.xml",
        "journaux": "Journals.xml",
        "operations TVA": "VATOperations.xml",
        "regimes TVA": "VATSchemes.xml",
        "historiques TVA": "VATVintages.xml",
        "parametrage bancaire": "BankOperationSettings.xml",
        "guides de saisie": "GuideModels.xml",
    }
    invoicing_references = {
        "taux TVA": "*Vats.xml",
        "types de paiement": "*PaymentTypes.xml",
        "modes de reglement": "*SettlementModes.xml",
        "devises": "*Currencies.xml",
        "codes activite": "*Nafs.xml",
    }

    return {
        "source_summary": "Referentiels locaux analyses pour definir le minimum fonctionnel.",
        "installed": reference_dir.exists(),
        "accounting_data": accounting_data.exists(),
        "invoicing_data": invoicing_data.exists(),
        "accounting_reference_files": [
            label
            for label, filename in accounting_references.items()
            if (accounting_data / filename).exists()
        ],
        "invoicing_reference_files": [
            label
            for label, pattern in invoicing_references.items()
            if any(invoicing_data.glob(pattern))
        ],
    }


def _get_dossier_or_404(db: Session, dossier_id: int) -> Dossier:
    dossier = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not dossier:
        raise HTTPException(404, "Dossier introuvable")
    return dossier


def _setup_status(db: Session, dossier_id: int) -> schemas.AccountingSetupStatus:
    fiscal_years = db.query(models.AccountingFiscalYear).filter_by(dossier_id=dossier_id).count()
    journals = db.query(models.AccountingJournal).filter_by(dossier_id=dossier_id).count()
    accounts = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id).count()
    entries = db.query(models.AccountingEntry).filter_by(dossier_id=dossier_id).count()
    return schemas.AccountingSetupStatus(
        dossier_id=dossier_id,
        fiscal_years=fiscal_years,
        journals=journals,
        accounts=accounts,
        entries=entries,
        ready=fiscal_years > 0 and journals > 0 and accounts > 0,
    )


def _publish_accounting_changed(dossier_id: int, action: str) -> None:
    events_manager.publish_nowait(
        make_event(
            {
                "type": "accounting_changed",
                "dossier_id": dossier_id,
                "action": action,
            }
        )
    )


def _audit(
    db: Session,
    dossier_id: int,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    details: str | None = None,
) -> None:
    db.add(
        models.AccountingAuditLog(
            dossier_id=dossier_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
        )
    )


def _vat_summary(db: Session, dossier_id: int) -> schemas.VatSummary:
    collected = Decimal("0.00")
    deductible = Decimal("0.00")

    lines = (
        db.query(models.AccountingEntryLine)
        .join(models.AccountingEntry, models.AccountingEntry.id == models.AccountingEntryLine.entry_id)
        .filter(models.AccountingEntry.dossier_id == dossier_id)
        .all()
    )
    for line in lines:
        number = line.account_number or ""
        amount = Decimal(line.credit or 0) - Decimal(line.debit or 0)
        if number.startswith("4457"):
            collected += amount
        elif number.startswith("4456"):
            deductible += -amount

    return schemas.VatSummary(
        collected_vat=collected,
        deductible_vat=deductible,
        net_vat_due=collected - deductible,
    )


def _control_issues(db: Session, dossier_id: int) -> list[schemas.AccountingControlIssue]:
    issues = []

    draft_entries = db.query(models.AccountingEntry).filter_by(dossier_id=dossier_id, status="draft").count()
    if draft_entries:
        issues.append(
            schemas.AccountingControlIssue(
                severity="warning",
                code="draft_entries",
                message="Ecritures encore en brouillon",
                count=draft_entries,
            )
        )

    unmatched_bank = (
        db.query(models.BankTransaction)
        .filter_by(dossier_id=dossier_id, reconciliation_status="unmatched")
        .count()
    )
    if unmatched_bank:
        issues.append(
            schemas.AccountingControlIssue(
                severity="warning",
                code="unmatched_bank",
                message="Operations bancaires non rapprochees",
                count=unmatched_bank,
            )
        )

    pending_invoices = (
        db.query(models.ElectronicInvoice)
        .filter(
            models.ElectronicInvoice.dossier_id == dossier_id,
            models.ElectronicInvoice.platform_status.in_(("draft", "pending", "error")),
        )
        .count()
    )
    if pending_invoices:
        issues.append(
            schemas.AccountingControlIssue(
                severity="warning",
                code="einvoice_pending",
                message="Factures electroniques a transmettre ou a corriger",
                count=pending_invoices,
            )
        )

    unbalanced_entries = 0
    entries = db.query(models.AccountingEntry).filter_by(dossier_id=dossier_id).all()
    for entry in entries:
        total_debit = sum(Decimal(line.debit or 0) for line in entry.lines)
        total_credit = sum(Decimal(line.credit or 0) for line in entry.lines)
        if total_debit.quantize(Decimal("0.01")) != total_credit.quantize(Decimal("0.01")):
            unbalanced_entries += 1

    if unbalanced_entries:
        issues.append(
            schemas.AccountingControlIssue(
                severity="error",
                code="unbalanced_entries",
                message="Ecritures desequilibrees",
                count=unbalanced_entries,
            )
        )

    return issues


def bootstrap_accounting_data(db: Session, dossier_id: int) -> schemas.AccountingSetupStatus:
    _get_dossier_or_404(db, dossier_id)

    today = date.today()
    label = str(today.year)
    changed = False
    fiscal_year = (
        db.query(models.AccountingFiscalYear)
        .filter_by(dossier_id=dossier_id, label=label)
        .first()
    )
    if fiscal_year is None:
        db.add(
            models.AccountingFiscalYear(
                dossier_id=dossier_id,
                label=label,
                start_date=date(today.year, 1, 1),
                end_date=date(today.year, 12, 31),
                status="open",
            )
        )
        changed = True

    existing_journals = {
        row.code
        for row in db.query(models.AccountingJournal).filter_by(dossier_id=dossier_id)
    }

    # Sécurité: certains environnements peuvent avoir des journaux dupliqués
    # si le bootstrap a déjà été relancé partiellement. On ignore les codes
    # déjà présents pour éviter les erreurs UNIQUE.
    for code, label, journal_type in DEFAULT_JOURNALS:
        if code in existing_journals:
            continue

        journal = models.AccountingJournal(
            dossier_id=dossier_id,
            code=code,
            label=label,
            journal_type=journal_type,
        )
        db.add(journal)
        existing_journals.add(code)
        changed = True

    existing_accounts = {
        row.number for row in db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id)
    }
    pcg_accounts = _read_pcg_text_accounts()
    template_accounts = DEFAULT_ACCOUNTS + pcg_accounts
    for number, label, account_class, account_type in template_accounts:
        if number not in existing_accounts:
            db.add(
                models.AccountingAccount(
                    dossier_id=dossier_id,
                    number=number,
                    label=label,
                    account_class=account_class,
                    account_type=account_type,
                )
            )
            existing_accounts.add(number)
            changed = True

    db.commit()
    status = _setup_status(db, dossier_id)
    if changed:
        _audit(db, dossier_id, "bootstrap", "accounting_setup", dossier_id)
        db.commit()
        _publish_accounting_changed(dossier_id, "bootstrap")
    return status


@router.get("/features")
def accounting_features():
    return {
        "inventory": _reference_inventory(),
        "catalog": [
            schemas.AccountingFeatureCatalog(
                source="Referentiel fonctionnel local",
                title="Minimum fonctionnel attendu",
                items=REFERENCE_FEATURES,
            ),
            schemas.AccountingFeatureCatalog(
                source="ERP Rosan 2026",
                title="Fonctions modernes a construire",
                items=ERP_2026_FEATURES,
            ),
        ],
    }


@router.get("/dossiers/{dossier_id}/status-2026", response_model=schemas.Accounting2026Status)
def accounting_2026_status(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    invoices = db.query(models.ElectronicInvoice).filter_by(dossier_id=dossier_id).count()
    invoices_pending = (
        db.query(models.ElectronicInvoice)
        .filter(
            models.ElectronicInvoice.dossier_id == dossier_id,
            models.ElectronicInvoice.platform_status.in_(("draft", "pending", "error")),
        )
        .count()
    )
    bank_transactions = db.query(models.BankTransaction).filter_by(dossier_id=dossier_id).count()
    bank_unmatched = (
        db.query(models.BankTransaction)
        .filter_by(dossier_id=dossier_id, reconciliation_status="unmatched")
        .count()
    )
    audit_events = db.query(models.AccountingAuditLog).filter_by(dossier_id=dossier_id).count()
    return schemas.Accounting2026Status(
        dossier_id=dossier_id,
        setup=_setup_status(db, dossier_id),
        invoices=invoices,
        invoices_pending_platform=invoices_pending,
        bank_transactions=bank_transactions,
        bank_unmatched=bank_unmatched,
        audit_events=audit_events,
        vat=_vat_summary(db, dossier_id),
        controls=_control_issues(db, dossier_id),
    )


@router.get("/dossiers/{dossier_id}/setup", response_model=schemas.AccountingSetupStatus)
def get_setup_status(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return _setup_status(db, dossier_id)


@router.post("/dossiers/{dossier_id}/bootstrap", response_model=schemas.AccountingSetupStatus)
def bootstrap_accounting(dossier_id: int, db: Session = Depends(get_db)):
    return bootstrap_accounting_data(db, dossier_id)


@router.get("/dossiers/{dossier_id}/journals", response_model=list[schemas.Journal])
def list_journals(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.AccountingJournal)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingJournal.code)
        .all()
    )


@router.post("/dossiers/{dossier_id}/journals", response_model=schemas.Journal)
def create_journal(dossier_id: int, data: schemas.JournalCreate, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    if not data.code or not data.label.strip():
        raise HTTPException(400, "Code et libelle du journal obligatoires")

    exists = db.query(models.AccountingJournal).filter_by(dossier_id=dossier_id, code=data.code).first()
    if exists:
        raise HTTPException(409, "Un journal existe deja avec ce code")

    journal = models.AccountingJournal(dossier_id=dossier_id, **data.model_dump())
    db.add(journal)
    db.commit()
    db.refresh(journal)
    _audit(db, dossier_id, "created", "journal", journal.id, journal.code)
    db.commit()
    _publish_accounting_changed(dossier_id, "journal_created")
    return journal


@router.get("/dossiers/{dossier_id}/accounts", response_model=list[schemas.Account])
def list_accounts(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.AccountingAccount)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingAccount.number)
        .all()
    )


@router.post("/dossiers/{dossier_id}/accounts", response_model=schemas.Account)
def create_account(dossier_id: int, data: schemas.AccountCreate, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    if not data.number or not data.label.strip():
        raise HTTPException(400, "Numero et intitule du compte obligatoires")

    exists = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id, number=data.number).first()
    if exists:
        raise HTTPException(409, "Un compte existe deja avec ce numero")

    account = models.AccountingAccount(dossier_id=dossier_id, **data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    _audit(db, dossier_id, "created", "account", account.id, account.number)
    db.commit()
    _publish_accounting_changed(dossier_id, "account_created")
    return account


@router.put("/dossiers/{dossier_id}/accounts/{account_id}", response_model=schemas.Account)
def update_account(
    dossier_id: int,
    account_id: int,
    data: schemas.AccountCreate,
    db: Session = Depends(get_db),
):
    _get_dossier_or_404(db, dossier_id)
    account = (
        db.query(models.AccountingAccount)
        .filter_by(dossier_id=dossier_id, id=account_id)
        .first()
    )
    if account is None:
        raise HTTPException(404, "Compte introuvable")

    if not data.number or not data.label.strip():
        raise HTTPException(400, "Numero et intitule du compte obligatoires")

    exists = (
        db.query(models.AccountingAccount)
        .filter(
            models.AccountingAccount.dossier_id == dossier_id,
            models.AccountingAccount.number == data.number,
            models.AccountingAccount.id != account_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(409, "Un compte existe deja avec ce numero")

    for key, value in data.model_dump().items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    _audit(db, dossier_id, "updated", "account", account.id, account.number)
    db.commit()
    _publish_accounting_changed(dossier_id, "account_updated")
    return account


@router.delete("/dossiers/{dossier_id}/accounts/{account_id}")
def delete_account(dossier_id: int, account_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    account = (
        db.query(models.AccountingAccount)
        .filter_by(dossier_id=dossier_id, id=account_id)
        .first()
    )
    if account is None:
        raise HTTPException(404, "Compte introuvable")

    used = (
        db.query(models.AccountingEntryLine)
        .join(models.AccountingEntry, models.AccountingEntry.id == models.AccountingEntryLine.entry_id)
        .filter(
            models.AccountingEntry.dossier_id == dossier_id,
            models.AccountingEntryLine.account_number == account.number,
        )
        .count()
    )
    if used:
        raise HTTPException(409, "Ce compte est utilisé dans des écritures")

    db.delete(account)
    db.commit()
    _audit(db, dossier_id, "deleted", "account", account_id, account.number)
    db.commit()
    _publish_accounting_changed(dossier_id, "account_deleted")
    return {"message": "Compte supprimé"}


@router.get("/dossiers/{dossier_id}/invoices", response_model=list[schemas.Invoice])
def list_invoices(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.ElectronicInvoice)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.ElectronicInvoice.issue_date.desc(), models.ElectronicInvoice.id.desc())
        .all()
    )


@router.post("/dossiers/{dossier_id}/invoices", response_model=schemas.Invoice)
def create_invoice(dossier_id: int, data: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    if not data.invoice_number.strip() or not data.partner_name.strip():
        raise HTTPException(400, "Numero de facture et partenaire obligatoires")

    exists = (
        db.query(models.ElectronicInvoice)
        .filter_by(dossier_id=dossier_id, invoice_number=data.invoice_number)
        .first()
    )
    if exists:
        raise HTTPException(409, "Une facture existe deja avec ce numero")

    invoice = models.ElectronicInvoice(dossier_id=dossier_id, **data.model_dump())
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    _audit(db, dossier_id, "created", "electronic_invoice", invoice.id, invoice.invoice_number)
    db.commit()
    _publish_accounting_changed(dossier_id, "invoice_created")
    return invoice


@router.delete("/dossiers/{dossier_id}/invoices/{invoice_id}")
def delete_invoice(dossier_id: int, invoice_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    invoice = (
        db.query(models.ElectronicInvoice)
        .filter_by(dossier_id=dossier_id, id=invoice_id)
        .first()
    )
    if invoice is None:
        raise HTTPException(404, "Facture introuvable")

    invoice_number = invoice.invoice_number
    db.delete(invoice)
    db.commit()
    _audit(db, dossier_id, "deleted", "electronic_invoice", invoice_id, invoice_number)
    db.commit()
    _publish_accounting_changed(dossier_id, "invoice_deleted")
    return {"message": "Facture supprimée"}


@router.get("/dossiers/{dossier_id}/bank-transactions", response_model=list[schemas.BankTransaction])
def list_bank_transactions(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.BankTransaction)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.BankTransaction.transaction_date.desc(), models.BankTransaction.id.desc())
        .all()
    )


@router.post("/dossiers/{dossier_id}/bank-transactions", response_model=schemas.BankTransaction)
def create_bank_transaction(
    dossier_id: int,
    data: schemas.BankTransactionCreate,
    db: Session = Depends(get_db),
):
    _get_dossier_or_404(db, dossier_id)
    if not data.label.strip():
        raise HTTPException(400, "Libelle bancaire obligatoire")

    transaction = models.BankTransaction(dossier_id=dossier_id, **data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    _audit(db, dossier_id, "created", "bank_transaction", transaction.id, transaction.label)
    db.commit()
    _publish_accounting_changed(dossier_id, "bank_transaction_created")
    return transaction


@router.delete("/dossiers/{dossier_id}/bank-transactions/{transaction_id}")
def delete_bank_transaction(dossier_id: int, transaction_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    transaction = (
        db.query(models.BankTransaction)
        .filter_by(dossier_id=dossier_id, id=transaction_id)
        .first()
    )
    if transaction is None:
        raise HTTPException(404, "Operation bancaire introuvable")

    label = transaction.label
    db.delete(transaction)
    db.commit()
    _audit(db, dossier_id, "deleted", "bank_transaction", transaction_id, label)
    db.commit()
    _publish_accounting_changed(dossier_id, "bank_transaction_deleted")
    return {"message": "Operation bancaire supprimée"}


@router.get("/dossiers/{dossier_id}/audit-log", response_model=list[schemas.AuditLog])
def list_audit_log(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.AccountingAuditLog)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingAuditLog.created_at.desc(), models.AccountingAuditLog.id.desc())
        .limit(500)
        .all()
    )


@router.get("/dossiers/{dossier_id}/vat-summary", response_model=schemas.VatSummary)
def vat_summary(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return _vat_summary(db, dossier_id)


@router.get("/dossiers/{dossier_id}/controls", response_model=list[schemas.AccountingControlIssue])
def accounting_controls(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return _control_issues(db, dossier_id)


@router.get("/dossiers/{dossier_id}/fec", response_class=PlainTextResponse)
def export_fec(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    journals = {
        journal.id: journal
        for journal in db.query(models.AccountingJournal).filter_by(dossier_id=dossier_id)
    }
    entries = (
        db.query(models.AccountingEntry)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingEntry.entry_date.asc(), models.AccountingEntry.id.asc())
        .all()
    )

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter="\t", lineterminator="\n")
    writer.writerow(
        [
            "JournalCode",
            "JournalLib",
            "EcritureNum",
            "EcritureDate",
            "CompteNum",
            "CompteLib",
            "CompAuxNum",
            "CompAuxLib",
            "PieceRef",
            "PieceDate",
            "EcritureLib",
            "Debit",
            "Credit",
            "EcritureLet",
            "DateLet",
            "ValidDate",
            "Montantdevise",
            "Idevise",
        ]
    )
    accounts = {
        account.number: account.label
        for account in db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id)
    }
    for entry in entries:
        journal = journals.get(entry.journal_id)
        for line in sorted(entry.lines, key=lambda item: item.id):
            writer.writerow(
                [
                    journal.code if journal else "",
                    journal.label if journal else "",
                    entry.id,
                    entry.entry_date.strftime("%Y%m%d"),
                    line.account_number,
                    accounts.get(line.account_number, ""),
                    line.third_party or "",
                    "",
                    entry.piece_number or "",
                    (entry.document_date or entry.entry_date).strftime("%Y%m%d"),
                    line.label or entry.label,
                    f"{Decimal(line.debit or 0):.2f}",
                    f"{Decimal(line.credit or 0):.2f}",
                    "",
                    "",
                    entry.created_at.strftime("%Y%m%d") if entry.created_at else "",
                    "",
                    "",
                ]
            )

    _audit(db, dossier_id, "exported", "fec", dossier_id)
    db.commit()
    return buffer.getvalue()


@router.get("/dossiers/{dossier_id}/fiscal-years", response_model=list[schemas.FiscalYear])
def list_fiscal_years(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.AccountingFiscalYear)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingFiscalYear.start_date.desc())
        .all()
    )


@router.post("/dossiers/{dossier_id}/entries", response_model=schemas.Entry)
def create_entry(dossier_id: int, data: schemas.EntryCreate, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)

    if len(data.lines) < 2:
        raise HTTPException(400, "Une ecriture doit contenir au moins deux lignes")

    fiscal_year = (
        db.query(models.AccountingFiscalYear)
        .filter_by(id=data.fiscal_year_id, dossier_id=dossier_id)
        .first()
    )
    if fiscal_year is None:
        raise HTTPException(404, "Exercice introuvable pour ce dossier")
    if fiscal_year.status != "open":
        raise HTTPException(409, "L'exercice n'est pas ouvert")

    journal = (
        db.query(models.AccountingJournal)
        .filter_by(id=data.journal_id, dossier_id=dossier_id, is_active=True)
        .first()
    )
    if journal is None:
        raise HTTPException(404, "Journal introuvable ou inactif pour ce dossier")

    total_debit = sum((line.debit for line in data.lines), Decimal("0.00"))
    total_credit = sum((line.credit for line in data.lines), Decimal("0.00"))
    if total_debit.quantize(Decimal("0.01")) != total_credit.quantize(Decimal("0.01")):
        raise HTTPException(400, "Ecriture non equilibree: debit different du credit")

    entry = models.AccountingEntry(
        dossier_id=dossier_id,
        fiscal_year_id=data.fiscal_year_id,
        journal_id=data.journal_id,
        entry_date=data.entry_date,
        document_date=data.document_date,
        piece_number=data.piece_number,
        label=data.label.strip(),
        source=data.source,
        status=data.status,
    )

    for line in data.lines:
        if line.debit < 0 or line.credit < 0:
            raise HTTPException(400, "Debit et credit doivent etre positifs")
        if line.debit and line.credit:
            raise HTTPException(400, "Une ligne ne peut pas avoir debit et credit")

        account = (
            db.query(models.AccountingAccount)
            .filter_by(dossier_id=dossier_id, number=line.account_number, is_active=True)
            .first()
        )
        if account is None:
            raise HTTPException(404, f"Compte introuvable: {line.account_number}")

        entry.lines.append(
            models.AccountingEntryLine(
                account_id=account.id,
                account_number=account.number,
                third_party=line.third_party,
                label=line.label,
                debit=line.debit,
                credit=line.credit,
                vat_code=line.vat_code,
            )
        )

    db.add(entry)
    db.commit()
    db.refresh(entry)
    _audit(db, dossier_id, "created", "entry", entry.id, entry.label)
    db.commit()
    _publish_accounting_changed(dossier_id, "entry_created")
    return entry


@router.get("/dossiers/{dossier_id}/entries", response_model=list[schemas.Entry])
def list_entries(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    return (
        db.query(models.AccountingEntry)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingEntry.entry_date.desc(), models.AccountingEntry.id.desc())
        .all()
    )


@router.get("/dossiers/{dossier_id}/trial-balance", response_model=list[schemas.TrialBalanceRow])
def trial_balance(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    accounts = (
        db.query(models.AccountingAccount)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingAccount.number)
        .all()
    )
    labels = {account.number: account.label for account in accounts}
    totals = {
        account.number: {
            "debit": Decimal("0.00"),
            "credit": Decimal("0.00"),
        }
        for account in accounts
    }

    lines = (
        db.query(models.AccountingEntryLine)
        .join(models.AccountingEntry, models.AccountingEntry.id == models.AccountingEntryLine.entry_id)
        .filter(models.AccountingEntry.dossier_id == dossier_id)
        .all()
    )
    for line in lines:
        totals.setdefault(
            line.account_number,
            {"debit": Decimal("0.00"), "credit": Decimal("0.00")},
        )
        totals[line.account_number]["debit"] += Decimal(line.debit or 0)
        totals[line.account_number]["credit"] += Decimal(line.credit or 0)

    return [
        schemas.TrialBalanceRow(
            account_number=number,
            account_label=labels.get(number, ""),
            debit=values["debit"],
            credit=values["credit"],
            balance=values["debit"] - values["credit"],
        )
        for number, values in totals.items()
        if values["debit"] or values["credit"]
    ]


@router.get("/dossiers/{dossier_id}/ledger", response_model=list[schemas.LedgerLine])
def ledger(dossier_id: int, db: Session = Depends(get_db)):
    _get_dossier_or_404(db, dossier_id)
    accounts = {
        account.number: account.label
        for account in db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id)
    }
    journals = {
        journal.id: journal.code
        for journal in db.query(models.AccountingJournal).filter_by(dossier_id=dossier_id)
    }

    entries = (
        db.query(models.AccountingEntry)
        .filter_by(dossier_id=dossier_id)
        .order_by(models.AccountingEntry.entry_date.asc(), models.AccountingEntry.id.asc())
        .all()
    )

    running_balances: dict[str, Decimal] = {}
    result = []
    for entry in entries:
        for line in sorted(entry.lines, key=lambda item: item.id):
            running_balances.setdefault(line.account_number, Decimal("0.00"))
            running_balances[line.account_number] += Decimal(line.debit or 0) - Decimal(line.credit or 0)
            result.append(
                schemas.LedgerLine(
                    entry_id=entry.id,
                    entry_date=entry.entry_date,
                    journal_code=journals.get(entry.journal_id, ""),
                    piece_number=entry.piece_number,
                    account_number=line.account_number,
                    account_label=accounts.get(line.account_number, ""),
                    label=line.label or entry.label,
                    debit=Decimal(line.debit or 0),
                    credit=Decimal(line.credit or 0),
                    balance=running_balances[line.account_number],
                )
            )

    return result


# ============================================================================
# === NOUVELLES FONCTIONS POUR ETATS FINANCIERS ET EXPORTS ===
# ============================================================================

def _get_account_category(account_number: str) -> str:
    """Determine la categorie comptable d'un compte selon son numero"""
    if account_number.startswith("1"):
        return "equity"  # Capitaux propres
    elif account_number.startswith("2") or account_number.startswith("3"):
        return "asset"  # Immobilisations / Stocks
    elif account_number.startswith("4") and not account_number.startswith("44"):
        return "asset" if account_number.startswith("41") else "liability"  # Clients/Fournisseurs
    elif account_number.startswith("5"):
        return "asset"  # Tresorerie
    elif account_number.startswith("6"):
        return "expense"  # Charges
    elif account_number.startswith("7"):
        return "revenue"  # Produits
    elif account_number.startswith("44"):
        return "liability"  # TVA et taxes
    return "other"


def _calculate_balance_sheet(db: Session, dossier_id: int, start_date: date, end_date: date) -> schemas.BalanceSheetSummary:
    """Calcule le bilan pour une periode donnee"""
    accounts = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id).all()
    
    totals = {}
    for account in accounts:
        lines = (
            db.query(models.AccountingEntryLine)
            .join(models.AccountingEntry)
            .filter(
                models.AccountingEntry.dossier_id == dossier_id,
                models.AccountingEntry.entry_date >= start_date,
                models.AccountingEntry.entry_date <= end_date,
                models.AccountingEntryLine.account_number == account.number
            )
            .all()
        )
        
        debit_total = sum(Decimal(line.debit or 0) for line in lines)
        credit_total = sum(Decimal(line.credit or 0) for line in lines)
        
        totals[account.number] = {
            "label": account.label,
            "debit": debit_total,
            "credit": credit_total,
            "category": _get_account_category(account.number)
        }
    
    total_assets = Decimal("0.00")
    total_liabilities = Decimal("0.00")
    total_equity = Decimal("0.00")
    
    for number, data in totals.items():
        net = data["debit"] - data["credit"]
        if data["category"] == "asset":
            total_assets += abs(net)
        elif data["category"] == "liability":
            total_liabilities += abs(net)
        elif data["category"] == "equity":
            total_equity += abs(net)
    
    # Resultat de l'exercice = Produits - Charges
    revenues_total = sum(
        totals[n]["credit"] - totals[n]["debit"] 
        for n in totals if totals[n]["category"] == "revenue"
    )
    expenses_total = sum(
        totals[n]["debit"] - totals[n]["credit"] 
        for n in totals if totals[n]["category"] == "expense"
    )
    net_income = revenues_total - expenses_total
    
    return schemas.BalanceSheetSummary(
        total_assets=total_assets.quantize(Decimal("0.01")),
        total_liabilities=total_liabilities.quantize(Decimal("0.01")),
        total_equity=total_equity.quantize(Decimal("0.01")),
        net_income=Decimal(str(net_income)).quantize(Decimal("0.01")),
        balance_check=abs(total_assets - (total_liabilities + total_equity + Decimal(str(net_income)))) < Decimal("0.01")
    )


def _calculate_income_statement(db: Session, dossier_id: int, start_date: date, end_date: date) -> schemas.IncomeStatementSummary:
    """Calcule le compte de resultat pour une periode donnee"""
    accounts = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id).all()
    
    total_revenues = Decimal("0.00")
    total_expenses = Decimal("0.00")
    
    for account in accounts:
        lines = (
            db.query(models.AccountingEntryLine)
            .join(models.AccountingEntry)
            .filter(
                models.AccountingEntry.dossier_id == dossier_id,
                models.AccountingEntry.entry_date >= start_date,
                models.AccountingEntry.entry_date <= end_date,
                models.AccountingEntryLine.account_number == account.number
            )
            .all()
        )
        
        debit_total = sum(Decimal(line.debit or 0) for line in lines)
        credit_total = sum(Decimal(line.credit or 0) for line in lines)
        
        if account.number.startswith("7"):
            total_revenues += credit_total - debit_total
        elif account.number.startswith("6"):
            total_expenses += debit_total - credit_total
    
    gross_profit = total_revenues - total_expenses
    
    return schemas.IncomeStatementSummary(
        total_revenues=total_revenues.quantize(Decimal("0.01")),
        total_expenses=total_expenses.quantize(Decimal("0.01")),
        gross_profit=gross_profit.quantize(Decimal("0.01")),
        operating_result=gross_profit,  # Simplifie
        net_result=gross_profit  # Simplifie (sans impots et autres elements)
    )


def _calculate_cash_flow(db: Session, dossier_id: int, start_date: date, end_date: date) -> schemas.CashFlowSummary:
    """Calcule le tableau de flux de tresorerie simplifie"""
    # Flux d'exploitation: variation des comptes clients/fournisseurs
    operating_flows = Decimal("0.00")
    investing_flows = Decimal("0.00")
    financing_flows = Decimal("0.00")
    
    accounts = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id).all()
    
    for account in accounts:
        lines = (
            db.query(models.AccountingEntryLine)
            .join(models.AccountingEntry)
            .filter(
                models.AccountingEntry.dossier_id == dossier_id,
                models.AccountingEntry.entry_date >= start_date,
                models.AccountingEntry.entry_date <= end_date,
                models.AccountingEntryLine.account_number == account.number
            )
            .all()
        )
        
        net = sum(Decimal(line.credit or 0) - Decimal(line.debit or 0) for line in lines)
        
        if account.number.startswith("5"):
            # Tresorerie - on ne l'inclut pas dans les flux mais pour calcul final
            pass
        elif account.number.startswith("41"):
            operating_flows -= net  # Variation clients
        elif account.number.startswith("40"):
            operating_flows += net  # Variation fournisseurs
        elif account.number.startswith("2"):
            investing_flows -= net  # Immobilisations
        elif account.number.startswith("1"):
            financing_flows += net  # Capitaux propres
    
    # Solde de tresorerie debut/fin de periode
    bank_lines_start = (
        db.query(models.AccountingEntryLine)
        .join(models.AccountingEntry)
        .filter(
            models.AccountingEntry.dossier_id == dossier_id,
            models.AccountingEntry.entry_date < start_date,
            models.AccountingEntryLine.account_number.like("5%")
        )
        .all()
    )
    opening_balance = sum(Decimal(line.debit or 0) - Decimal(line.credit or 0) for line in bank_lines_start)
    
    bank_lines_end = (
        db.query(models.AccountingEntryLine)
        .join(models.AccountingEntry)
        .filter(
            models.AccountingEntry.dossier_id == dossier_id,
            models.AccountingEntry.entry_date <= end_date,
            models.AccountingEntryLine.account_number.like("5%")
        )
        .all()
    )
    closing_balance = sum(Decimal(line.debit or 0) - Decimal(line.credit or 0) for line in bank_lines_end)
    
    net_change = closing_balance - opening_balance
    
    return schemas.CashFlowSummary(
        operating_cash_flow=Decimal(str(operating_flows)).quantize(Decimal("0.01")),
        investing_cash_flow=Decimal(str(investing_flows)).quantize(Decimal("0.01")),
        financing_cash_flow=Decimal(str(financing_flows)).quantize(Decimal("0.01")),
        net_cash_change=Decimal(str(net_change)).quantize(Decimal("0.01")),
        opening_balance=Decimal(str(opening_balance)).quantize(Decimal("0.01")),
        closing_balance=Decimal(str(closing_balance)).quantize(Decimal("0.01"))
    )


def _generate_pdf_report(
    title: str,
    dossier_name: str,
    period_start: date,
    period_end: date,
    data_rows: list[list],
    headers: list[str],
    summary_data: dict | None = None
) -> bytes:
    """Genere un rapport PDF professionnel"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Titre
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(f"Dossier: {dossier_name}", styles['Normal']))
    elements.append(Paragraph(f"Periode: {period_start.strftime('%d/%m/%Y')} au {period_end.strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    # Resume si present
    if summary_data:
        summary_table_data = [["Indicateur", "Valeur"]]
        for key, value in summary_data.items():
            summary_table_data.append([key.replace("_", " ").title(), f"{value:.2f} €"])
        
        summary_table = Table(summary_table_data, colWidths=[5*cm, 3*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*cm))
    
    # Tableau principal
    table_data = [headers] + data_rows
    table = Table(table_data, colWidths=[3*cm, 6*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    return pdf_content


@router.get("/dossiers/{dossier_id}/balance-sheet", response_model=schemas.BalanceSheetSummary)
def get_balance_sheet(
    dossier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Recupere le bilan pour une periode"""
    _get_dossier_or_404(db, dossier_id)
    
    if not start_date or not end_date:
        today = date.today()
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    return _calculate_balance_sheet(db, dossier_id, start_date, end_date)


@router.get("/dossiers/{dossier_id}/income-statement", response_model=schemas.IncomeStatementSummary)
def get_income_statement(
    dossier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Recupere le compte de resultat pour une periode"""
    _get_dossier_or_404(db, dossier_id)
    
    if not start_date or not end_date:
        today = date.today()
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    return _calculate_income_statement(db, dossier_id, start_date, end_date)


@router.get("/dossiers/{dossier_id}/cash-flow", response_model=schemas.CashFlowSummary)
def get_cash_flow(
    dossier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Recupere le tableau de flux de tresorerie pour une periode"""
    _get_dossier_or_404(db, dossier_id)
    
    if not start_date or not end_date:
        today = date.today()
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    return _calculate_cash_flow(db, dossier_id, start_date, end_date)


@router.get("/dossiers/{dossier_id}/dashboard", response_model=schemas.FinancialDashboard)
def get_financial_dashboard(
    dossier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Recupere le tableau de bord financier complet"""
    _get_dossier_or_404(db, dossier_id)
    
    if not start_date or not end_date:
        today = date.today()
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    # Calcul des indicateurs
    balance_summary = _calculate_balance_sheet(db, dossier_id, start_date, end_date)
    income_summary = _calculate_income_statement(db, dossier_id, start_date, end_date)
    cash_flow_summary = _calculate_cash_flow(db, dossier_id, start_date, end_date)
    
    # KPIs
    kpis = [
        schemas.DashboardKPI(
            name="Chiffre d'affaires",
            value=income_summary.total_revenues,
            unit="EUR",
            trend="up" if income_summary.total_revenues > 0 else "stable"
        ),
        schemas.DashboardKPI(
            name="Resultat net",
            value=income_summary.net_result,
            unit="EUR",
            trend="up" if income_summary.net_result > 0 else "down"
        ),
        schemas.DashboardKPI(
            name="Tresorerie fin de periode",
            value=cash_flow_summary.closing_balance,
            unit="EUR"
        ),
        schemas.DashboardKPI(
            name="TVA a payer",
            value=_vat_summary(db, dossier_id).net_vat_due,
            unit="EUR"
        ),
        schemas.DashboardKPI(
            name="Total Actif",
            value=balance_summary.total_assets,
            unit="EUR"
        ),
    ]
    
    return schemas.FinancialDashboard(
        dossier_id=dossier_id,
        period_start=start_date,
        period_end=end_date,
        kpis=kpis,
        balance_summary=balance_summary,
        income_summary=income_summary,
        cash_flow_summary=cash_flow_summary
    )


@router.get("/dossiers/{dossier_id}/reports/balance-sheet/pdf")
def export_balance_sheet_pdf(
    dossier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Export du bilan en PDF"""
    _get_dossier_or_404(db, dossier_id)
    
    if not start_date or not end_date:
        today = date.today()
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    dossier = db.query(Dossier).filter_by(id=dossier_id).first()
    summary = _calculate_balance_sheet(db, dossier_id, start_date, end_date)
    
    # Preparation des donnees pour le PDF
    accounts = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id).all()
    rows = []
    
    for account in accounts:
        lines = (
            db.query(models.AccountingEntryLine)
            .join(models.AccountingEntry)
            .filter(
                models.AccountingEntry.dossier_id == dossier_id,
                models.AccountingEntry.entry_date >= start_date,
                models.AccountingEntry.entry_date <= end_date,
                models.AccountingEntryLine.account_number == account.number
            )
            .all()
        )
        
        if lines:
            debit_total = sum(Decimal(line.debit or 0) for line in lines)
            credit_total = sum(Decimal(line.credit or 0) for line in lines)
            net = debit_total - credit_total
            category = _get_account_category(account.number)
            
            rows.append([
                account.number,
                account.label[:40],
                f"{debit_total:.2f}",
                f"{credit_total:.2f}",
                f"{net:.2f}"
            ])
    
    pdf_content = _generate_pdf_report(
        title="BILAN COMPTABLE",
        dossier_name=dossier.nom_entreprise if dossier else f"Dossier #{dossier_id}",
        period_start=start_date,
        period_end=end_date,
        data_rows=rows,
        headers=["Compte", "Libelle", "Debit", "Credit", "Solde"],
        summary_data={
            "Total Actif": float(summary.total_assets),
            "Total Passif": float(summary.total_liabilities),
            "Capitaux Propres": float(summary.total_equity),
            "Resultat Net": float(summary.net_income)
        }
    )
    
    _audit(db, dossier_id, "exported", "balance_sheet_pdf", dossier_id)
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=bilan_{dossier_id}_{end_date.strftime('%Y%m%d')}.pdf"}
    )


@router.get("/dossiers/{dossier_id}/reports/income-statement/pdf")
def export_income_statement_pdf(
    dossier_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """Export du compte de resultat en PDF"""
    _get_dossier_or_404(db, dossier_id)
    
    if not start_date or not end_date:
        today = date.today()
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    
    dossier = db.query(Dossier).filter_by(id=dossier_id).first()
    summary = _calculate_income_statement(db, dossier_id, start_date, end_date)
    
    # Preparation des donnees pour le PDF
    accounts = db.query(models.AccountingAccount).filter_by(dossier_id=dossier_id).all()
    rows = []
    
    for account in accounts:
        if account.number.startswith("6") or account.number.startswith("7"):
            lines = (
                db.query(models.AccountingEntryLine)
                .join(models.AccountingEntry)
                .filter(
                    models.AccountingEntry.dossier_id == dossier_id,
                    models.AccountingEntry.entry_date >= start_date,
                    models.AccountingEntry.entry_date <= end_date,
                    models.AccountingEntryLine.account_number == account.number
                )
                .all()
            )
            
            if lines:
                debit_total = sum(Decimal(line.debit or 0) for line in lines)
                credit_total = sum(Decimal(line.credit or 0) for line in lines)
                net = credit_total - debit_total if account.number.startswith("7") else debit_total - credit_total
                
                rows.append([
                    account.number,
                    account.label[:40],
                    f"{debit_total:.2f}",
                    f"{credit_total:.2f}",
                    f"{net:.2f}"
                ])
    
    pdf_content = _generate_pdf_report(
        title="COMPTE DE RESULTAT",
        dossier_name=dossier.nom_entreprise if dossier else f"Dossier #{dossier_id}",
        period_start=start_date,
        period_end=end_date,
        data_rows=rows,
        headers=["Compte", "Libelle", "Debit", "Credit", "Net"],
        summary_data={
            "Total Produits": float(summary.total_revenues),
            "Total Charges": float(summary.total_expenses),
            "Resultat Brut": float(summary.gross_profit),
            "Resultat Net": float(summary.net_result)
        }
    )
    
    _audit(db, dossier_id, "exported", "income_statement_pdf", dossier_id)
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=compte_resultat_{dossier_id}_{end_date.strftime('%Y%m%d')}.pdf"}
    )


@router.get("/dossiers/{dossier_id}/reports/trial-balance/csv")
def export_trial_balance_csv(
    dossier_id: int,
    db: Session = Depends(get_db)
):
    """Export de la balance comptable en CSV"""
    _get_dossier_or_404(db, dossier_id)
    
    trial_balance_data = trial_balance(dossier_id, db)
    
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(["Compte", "Libelle", "Debit", "Credit", "Solde"])
    
    for row in trial_balance_data:
        writer.writerow([
            row.account_number,
            row.account_label,
            f"{row.debit:.2f}",
            f"{row.credit:.2f}",
            f"{row.balance:.2f}"
        ])
    
    _audit(db, dossier_id, "exported", "trial_balance_csv", dossier_id)
    
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=balance_{dossier_id}.csv"}
    )


@router.get("/dossiers/{dossier_id}/reports/ledger/csv")
def export_ledger_csv(
    dossier_id: int,
    db: Session = Depends(get_db)
):
    """Export du grand livre en CSV"""
    _get_dossier_or_404(db, dossier_id)
    
    ledger_data = ledger(dossier_id, db)
    
    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=";", lineterminator="\n")
    writer.writerow(["Date", "Journal", "Piece", "Compte", "Libelle", "Debit", "Credit", "Solde"])
    
    for line in ledger_data:
        writer.writerow([
            line.entry_date.strftime("%Y-%m-%d"),
            line.journal_code,
            line.piece_number or "",
            line.account_number,
            line.label[:50],
            f"{line.debit:.2f}",
            f"{line.credit:.2f}",
            f"{line.balance:.2f}"
        ])
    
    _audit(db, dossier_id, "exported", "ledger_csv", dossier_id)
    
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=grand_livre_{dossier_id}.csv"}
    )
