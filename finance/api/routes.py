# -*- coding: utf-8 -*-
"""
API FastAPI pour le module Finance

Endpoints REST pour :
- Exercices comptables
- Journaux comptables
- Plan comptable
- Écritures comptables
- Trésorerie
- Rapports financiers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from core.db_postgresql import get_db_session
from finance.models.core import FiscalYear, AccountingJournal, AccountingAccount
from finance.models.entries import AccountingEntry
from finance.services.journal_entry_service import JournalEntryService, JournalEntryError
from finance.services.pcg_loader_service import PCGLoaderService

router = APIRouter(prefix="/finance", tags=["Finance"])


# =============================================================================
# EXERCICES COMPTABLES
# =============================================================================

@router.get("/fiscal-years", response_model=List[dict])
def list_fiscal_years(
    dossier_id: int = Query(..., description="ID du dossier"),
    db: Session = Depends(get_db_session)
):
    """Liste tous les exercices d'un dossier"""
    fiscal_years = db.query(FiscalYear).filter(
        FiscalYear.dossier_id == dossier_id
    ).order_by(FiscalYear.start_date.desc()).all()
    
    return [
        {
            "id": fy.id,
            "label": fy.label,
            "start_date": fy.start_date,
            "end_date": fy.end_date,
            "status": fy.status,
            "is_open": fy.is_open(),
        }
        for fy in fiscal_years
    ]


@router.post("/fiscal-years", status_code=status.HTTP_201_CREATED)
def create_fiscal_year(
    label: str,
    start_date: date,
    end_date: date,
    dossier_id: int,
    db: Session = Depends(get_db_session)
):
    """Crée un nouvel exercice comptable"""
    fiscal_year = FiscalYear(
        dossier_id=dossier_id,
        label=label,
        start_date=start_date,
        end_date=end_date,
        status="draft"
    )
    
    db.add(fiscal_year)
    db.commit()
    db.refresh(fiscal_year)
    
    return {"id": fiscal_year.id, "message": "Exercice créé avec succès"}


# =============================================================================
# JOURNAUX COMPTABLES
# =============================================================================

@router.get("/journals", response_model=List[dict])
def list_journals(
    dossier_id: int = Query(..., description="ID du dossier"),
    db: Session = Depends(get_db_session)
):
    """Liste tous les journaux d'un dossier"""
    journals = db.query(AccountingJournal).filter(
        AccountingJournal.dossier_id == dossier_id
    ).order_by(AccountingJournal.code).all()
    
    return [
        {
            "id": j.id,
            "code": j.code,
            "label": j.label,
            "journal_type": j.journal_type,
            "is_active": j.is_active,
            "last_entry_number": j.last_entry_number,
        }
        for j in journals
    ]


@router.post("/journals", status_code=status.HTTP_201_CREATED)
def create_journal(
    code: str,
    label: str,
    journal_type: str,
    dossier_id: int,
    fiscal_year_id: Optional[int] = None,
    db: Session = Depends(get_db_session)
):
    """Crée un nouveau journal comptable"""
    journal = AccountingJournal(
        dossier_id=dossier_id,
        fiscal_year_id=fiscal_year_id,
        code=code,
        label=label,
        journal_type=journal_type,
        is_active=True
    )
    
    db.add(journal)
    db.commit()
    db.refresh(journal)
    
    return {"id": journal.id, "message": "Journal créé avec succès"}


# =============================================================================
# PLAN COMPTABLE
# =============================================================================

@router.get("/accounts", response_model=List[dict])
def list_accounts(
    dossier_id: int = Query(..., description="ID du dossier"),
    search: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Liste les comptes du plan comptable"""
    query = db.query(AccountingAccount).filter(
        AccountingAccount.dossier_id == dossier_id,
        AccountingAccount.is_active == True
    )
    
    if search:
        query = query.filter(
            (AccountingAccount.number.contains(search)) |
            (AccountingAccount.label.ilike(f"%{search}%"))
        )
    
    accounts = query.order_by(AccountingAccount.number).all()
    
    return [
        {
            "id": a.id,
            "number": a.number,
            "label": a.label,
            "account_class": a.account_class,
            "account_type": a.account_type,
            "is_third_party": a.is_third_party,
        }
        for a in accounts
    ]


@router.post("/accounts/pcg/load")
def load_pcg(
    dossier_id: int,
    file_path: str = "/workspace/PCG géné.txt",
    overwrite: bool = False,
    db: Session = Depends(get_db_session)
):
    """Charge le Plan Comptable Général français"""
    try:
        service = PCGLoaderService(db)
        stats = service.load_from_file(dossier_id, file_path, overwrite)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# ÉCRITURES COMPTABLES
# =============================================================================

@router.get("/entries", response_model=List[dict])
def list_entries(
    dossier_id: int = Query(..., description="ID du dossier"),
    journal_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db_session)
):
    """Liste les écritures comptables avec filtres"""
    query = db.query(AccountingEntry).filter(
        AccountingEntry.dossier_id == dossier_id
    )
    
    if journal_id:
        query = query.filter(AccountingEntry.journal_id == journal_id)
    
    if status_filter:
        query = query.filter(AccountingEntry.status == status_filter)
    
    if date_from:
        query = query.filter(AccountingEntry.entry_date >= date_from)
    
    if date_to:
        query = query.filter(AccountingEntry.entry_date <= date_to)
    
    entries = query.order_by(AccountingEntry.entry_date.desc(), AccountingEntry.entry_number.desc()).all()
    
    return [
        {
            "id": e.id,
            "entry_number": e.entry_number,
            "journal_id": e.journal_id,
            "entry_date": e.entry_date,
            "label": e.label,
            "piece_number": e.piece_number,
            "status": e.status,
            "total_debit": float(e.total_debit),
            "total_credit": float(e.total_credit),
            "is_balanced": e.is_balanced,
            "lines_count": len(e.lines),
        }
        for e in entries
    ]


@router.post("/entries", status_code=status.HTTP_201_CREATED)
def create_entry(
    dossier_id: int,
    fiscal_year_id: int,
    journal_id: int,
    entry_date: date,
    label: str,
    lines: List[dict],
    piece_number: Optional[str] = None,
    document_date: Optional[date] = None,
    source: str = "manual",
    db: Session = Depends(get_db_session)
):
    """Crée une nouvelle écriture comptable"""
    try:
        service = JournalEntryService(db)
        entry = service.create_entry(
            dossier_id=dossier_id,
            fiscal_year_id=fiscal_year_id,
            journal_id=journal_id,
            entry_date=entry_date,
            label=label,
            lines=lines,
            piece_number=piece_number,
            document_date=document_date,
            source=source,
        )
        
        db.commit()
        db.refresh(entry)
        
        return {
            "id": entry.id,
            "entry_number": entry.entry_number,
            "message": "Écriture créée avec succès"
        }
    
    except JournalEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entries/{entry_id}/validate")
def validate_entry(
    entry_id: int,
    validated_by: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Valide une écriture (passage en statut 'posted')"""
    entry = db.query(AccountingEntry).filter(AccountingEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Écriture non trouvée")
    
    if entry.status != "draft":
        raise HTTPException(status_code=400, detail="Seules les écritures en brouillon peuvent être validées")
    
    try:
        service = JournalEntryService(db)
        service.validate_entry(entry, validated_by)
        db.commit()
        
        return {"message": "Écriture validée avec succès"}
    
    except JournalEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/entries/{entry_id}/cancel")
def cancel_entry(
    entry_id: int,
    cancellation_reason: str,
    db: Session = Depends(get_db_session)
):
    """Annule une écriture par contre-passation"""
    entry = db.query(AccountingEntry).filter(AccountingEntry.id == entry_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Écriture non trouvée")
    
    try:
        service = JournalEntryService(db)
        cancellation_entry = service.cancel_entry(entry, cancellation_reason)
        db.commit()
        
        return {
            "original_entry_id": entry_id,
            "cancellation_entry_id": cancellation_entry.id,
            "message": "Écriture annulée avec succès"
        }
    
    except JournalEntryError as e:
        raise HTTPException(status_code=400, detail=str(e))
