# -*- coding: utf-8 -*-
"""
Service de gestion des écritures comptables

Ce service encapsule toute la logique métier liée aux écritures :
- Création avec validation partie double
- Modification (seulement brouillons)
- Validation/Postage
- Annulation par contre-passation
- Suppression (seulement brouillons)
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from finance.models.entries import AccountingEntry, AccountingEntryLine
from finance.models.core import AccountingJournal, FiscalYear, AccountingAccount
from finance.models.audit import AuditLog


class JournalEntryError(Exception):
    """Exception personnalisée pour les erreurs d'écritures"""
    pass


class JournalEntryService:
    """
    Service de gestion des écritures comptables
    
    Toutes les opérations sur les écritures passent par ce service
    pour garantir l'intégrité des données et le respect des règles
    comptables (partie double, etc.)
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def create_entry(
        self,
        dossier_id: int,
        fiscal_year_id: int,
        journal_id: int,
        entry_date: date,
        label: str,
        lines: List[Dict],
        piece_number: Optional[str] = None,
        document_date: Optional[date] = None,
        source: str = "manual",
        source_id: Optional[int] = None,
        created_by: Optional[str] = None,
    ) -> AccountingEntry:
        """
        Crée une nouvelle écriture comptable
        
        Args:
            dossier_id : ID du dossier
            fiscal_year_id : ID de l'exercice
            journal_id : ID du journal
            entry_date : Date d'écriture
            label : Libellé général
            lines : Liste des lignes [{'account_id': X, 'debit': D, 'credit': C, 'label': L, 'third_party_code': T}, ...]
            piece_number : Numéro de pièce (optionnel)
            document_date : Date de pièce (optionnel)
            source : Origine (manual, invoice, etc.)
            source_id : ID dans la table source
            created_by : Utilisateur créateur
            
        Returns:
            AccountingEntry : L'écriture créée
            
        Raises:
            JournalEntryError : Si l'écriture n'est pas équilibrée
        """
        # Vérifier que l'exercice est ouvert
        fiscal_year = self.db.query(FiscalYear).filter(
            FiscalYear.id == fiscal_year_id
        ).first()
        
        if not fiscal_year:
            raise JournalEntryError(f"L'exercice {fiscal_year_id} n'existe pas")
        
        if not fiscal_year.is_open():
            raise JournalEntryError(
                f"Impossible de créer une écriture dans un exercice fermé ou en brouillon "
                f"(statut: {fiscal_year.status})"
            )
        
        # Vérifier que la date appartient à l'exercice
        if not fiscal_year.contains_date(entry_date):
            raise JournalEntryError(
                f"La date {entry_date} n'appartient pas à l'exercice "
                f"{fiscal_year.label} ({fiscal_year.start_date} - {fiscal_year.end_date})"
            )
        
        # Récupérer le journal
        journal = self.db.query(AccountingJournal).filter(
            AccountingJournal.id == journal_id
        ).first()
        
        if not journal:
            raise JournalEntryError(f"Le journal {journal_id} n'existe pas")
        
        if not journal.is_active:
            raise JournalEntryError(f"Le journal {journal.code} est inactif")
        
        # Calculer les totaux
        total_debit = sum(Decimal(str(line.get('debit', 0))) for line in lines)
        total_credit = sum(Decimal(str(line.get('credit', 0))) for line in lines)
        
        # Valider la partie double
        if total_debit != total_credit:
            raise JournalEntryError(
                f"Écriture déséquilibrée : Débit={total_debit} ≠ Crédit={total_credit}"
            )
        
        if total_debit == 0:
            raise JournalEntryError("Écriture avec montants nuls refusée")
        
        # Obtenir le prochain numéro d'écriture
        entry_number = journal.get_next_entry_number()
        
        # Créer l'écriture
        entry = AccountingEntry(
            dossier_id=dossier_id,
            fiscal_year_id=fiscal_year_id,
            journal_id=journal_id,
            entry_number=entry_number,
            piece_number=piece_number,
            label=label,
            entry_date=entry_date,
            document_date=document_date,
            source=source,
            source_id=source_id,
            status="draft",
            total_debit=total_debit,
            total_credit=total_credit,
            created_by=created_by,
        )
        
        self.db.add(entry)
        self.db.flush()  # Pour obtenir l'ID
        
        # Créer les lignes
        for idx, line_data in enumerate(lines, start=1):
            account = self.db.query(AccountingAccount).filter(
                AccountingAccount.id == line_data['account_id']
            ).first()
            
            if not account:
                raise JournalEntryError(
                    f"Le compte {line_data['account_id']} n'existe pas"
                )
            
            line = AccountingEntryLine(
                entry_id=entry.id,
                line_number=idx,
                account_id=account.id,
                account_number=account.number,
                account_label=account.label,
                debit=Decimal(str(line_data.get('debit', 0))),
                credit=Decimal(str(line_data.get('credit', 0))),
                third_party_code=line_data.get('third_party_code'),
                third_party_name=line_data.get('third_party_name'),
                label=line_data.get('label'),
                vat_code=line_data.get('vat_code'),
                vat_rate=line_data.get('vat_rate'),
                vat_amount=Decimal(str(line_data.get('vat_amount', 0))) if line_data.get('vat_amount') else None,
            )
            self.db.add(line)
        
        # Sauvegarder
        self.db.commit()
        self.db.refresh(entry)
        
        # Log d'audit
        AuditLog.log(
            db_session=self.db,
            action_type="CREATE",
            entity_type="AccountingEntry",
            entity_id=entry.id,
            entity_label=f"Écriture {entry.entry_number} - {label}",
            new_values={
                "dossier_id": dossier_id,
                "journal_id": journal_id,
                "entry_date": str(entry_date),
                "total_debit": str(total_debit),
                "total_credit": str(total_credit),
                "lines_count": len(lines),
            },
            user_login=created_by,
        )
        
        return entry

    def get_entry(self, entry_id: int) -> Optional[AccountingEntry]:
        """Récupère une écriture par son ID avec ses lignes"""
        return self.db.query(AccountingEntry).options(
            joinedload(AccountingEntry.lines),
            joinedload(AccountingEntry.journal),
            joinedload(AccountingEntry.fiscal_year),
        ).filter(AccountingEntry.id == entry_id).first()

    def update_entry(
        self,
        entry_id: int,
        label: Optional[str] = None,
        piece_number: Optional[str] = None,
        document_date: Optional[date] = None,
        lines: Optional[List[Dict]] = None,
        updated_by: Optional[str] = None,
    ) -> AccountingEntry:
        """
        Met à jour une écriture (seulement si brouillon)
        
        Args:
            entry_id : ID de l'écriture
            label : Nouveau libellé
            piece_number : Nouveau numéro de pièce
            document_date : Nouvelle date de pièce
            lines : Nouvelles lignes (remplace toutes les lignes existantes)
            updated_by : Utilisateur modificateur
            
        Returns:
            AccountingEntry : L'écriture mise à jour
            
        Raises:
            JournalEntryError : Si l'écriture n'est pas en brouillon
        """
        entry = self.get_entry(entry_id)
        
        if not entry:
            raise JournalEntryError(f"L'écriture {entry_id} n'existe pas")
        
        if not entry.is_draft:
            raise JournalEntryError(
                f"Impossible de modifier une écriture {entry.status}. "
                f"Seules les écritures en brouillon peuvent être modifiées."
            )
        
        # Sauvegarder les anciennes valeurs pour audit
        old_values = {
            "label": entry.label,
            "piece_number": entry.piece_number,
            "lines_count": len(entry.lines),
        }
        
        # Mettre à jour les champs simples
        if label:
            entry.label = label
        if piece_number:
            entry.piece_number = piece_number
        if document_date:
            entry.document_date = document_date
        
        # Mettre à jour les lignes si fournies
        if lines is not None:
            # Supprimer les anciennes lignes
            for line in entry.lines:
                self.db.delete(line)
            self.db.flush()
            
            # Recréer les nouvelles lignes
            total_debit = Decimal("0.00")
            total_credit = Decimal("0.00")
            
            for idx, line_data in enumerate(lines, start=1):
                account = self.db.query(AccountingAccount).filter(
                    AccountingAccount.id == line_data['account_id']
                ).first()
                
                if not account:
                    raise JournalEntryError(
                        f"Le compte {line_data['account_id']} n'existe pas"
                    )
                
                debit = Decimal(str(line_data.get('debit', 0)))
                credit = Decimal(str(line_data.get('credit', 0)))
                total_debit += debit
                total_credit += credit
                
                line = AccountingEntryLine(
                    entry_id=entry.id,
                    line_number=idx,
                    account_id=account.id,
                    account_number=account.number,
                    account_label=account.label,
                    debit=debit,
                    credit=credit,
                    third_party_code=line_data.get('third_party_code'),
                    third_party_name=line_data.get('third_party_name'),
                    label=line_data.get('label'),
                    vat_code=line_data.get('vat_code'),
                    vat_rate=line_data.get('vat_rate'),
                    vat_amount=Decimal(str(line_data.get('vat_amount', 0))) if line_data.get('vat_amount') else None,
                )
                self.db.add(line)
            
            # Vérifier l'équilibre
            if total_debit != total_credit:
                raise JournalEntryError(
                    f"Écriture déséquilibrée après modification : "
                    f"Débit={total_debit} ≠ Crédit={total_credit}"
                )
            
            entry.total_debit = total_debit
            entry.total_credit = total_credit
        
        self.db.commit()
        self.db.refresh(entry)
        
        # Log d'audit
        AuditLog.log(
            db_session=self.db,
            action_type="UPDATE",
            entity_type="AccountingEntry",
            entity_id=entry.id,
            entity_label=f"Écriture {entry.entry_number}",
            old_values=old_values,
            new_values={
                "label": entry.label,
                "piece_number": entry.piece_number,
                "lines_count": len(entry.lines),
            },
            user_login=updated_by,
        )
        
        return entry

    def validate_entry(self, entry_id: int, validated_by: Optional[str] = None) -> AccountingEntry:
        """
        Valide (poste) une écriture
        
        Args:
            entry_id : ID de l'écriture
            validated_by : Utilisateur validateur
            
        Returns:
            AccountingEntry : L'écriture validée
            
        Raises:
            JournalEntryError : Si l'écriture n'est pas en brouillon ou déséquilibrée
        """
        entry = self.get_entry(entry_id)
        
        if not entry:
            raise JournalEntryError(f"L'écriture {entry_id} n'existe pas")
        
        if not entry.is_draft:
            raise JournalEntryError(
                f"Seules les écritures en brouillon peuvent être validées "
                f"(statut actuel: {entry.status})"
            )
        
        # Vérifier l'équilibre
        entry.recalculate_totals()
        if not entry.is_balanced:
            raise JournalEntryError(
                f"Impossible de valider une écriture déséquilibrée : "
                f"Débit={entry.total_debit} ≠ Crédit={entry.total_credit}"
            )
        
        # Vérifier qu'il y a au moins 2 lignes
        if len(entry.lines) < 2:
            raise JournalEntryError(
                "Une écriture doit avoir au moins 2 lignes (débit et crédit)"
            )
        
        # Valider
        entry.status = "posted"
        entry.validated_by = validated_by
        entry.validated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(entry)
        
        # Log d'audit
        AuditLog.log(
            db_session=self.db,
            action_type="VALIDATE",
            entity_type="AccountingEntry",
            entity_id=entry.id,
            entity_label=f"Écriture {entry.entry_number}",
            new_values={"status": "posted", "validated_by": validated_by},
            user_login=validated_by,
        )
        
        return entry

    def cancel_entry(self, entry_id: int, cancelled_by: Optional[str] = None, 
                     cancellation_reason: Optional[str] = None) -> AccountingEntry:
        """
        Annule une écriture par contre-passation
        
        Crée une nouvelle écriture qui inverse débit et crédit.
        
        Args:
            entry_id : ID de l'écriture à annuler
            cancelled_by : Utilisateur annulateur
            cancellation_reason : Motif d'annulation
            
        Returns:
            AccountingEntry : La nouvelle écriture d'annulation
        """
        original_entry = self.get_entry(entry_id)
        
        if not original_entry:
            raise JournalEntryError(f"L'écriture {entry_id} n'existe pas")
        
        if original_entry.is_cancelled:
            raise JournalEntryError(f"L'écriture {entry_id} est déjà annulée")
        
        if original_entry.is_draft:
            # Si brouillon, on peut juste changer le statut
            original_entry.status = "cancelled"
            self.db.commit()
            
            AuditLog.log(
                db_session=self.db,
                action_type="CANCEL",
                entity_type="AccountingEntry",
                entity_id=original_entry.id,
                entity_label=f"Écriture {original_entry.entry_number}",
                new_values={"status": "cancelled", "reason": cancellation_reason},
                user_login=cancelled_by,
            )
            
            return original_entry
        
        # Pour une écriture validée, créer une contre-passation
        cancellation_lines = []
        for line in original_entry.lines:
            # Inverser débit et crédit
            cancellation_lines.append({
                'account_id': line.account_id,
                'debit': float(line.credit) if line.credit > 0 else 0,
                'credit': float(line.debit) if line.debit > 0 else 0,
                'label': f"Annulation de {line.label or original_entry.label}",
                'third_party_code': line.third_party_code,
            })
        
        # Créer l'écriture d'annulation
        cancellation_entry = self.create_entry(
            dossier_id=original_entry.dossier_id,
            fiscal_year_id=original_entry.fiscal_year_id,
            journal_id=original_entry.journal_id,
            entry_date=date.today(),
            label=f"ANNULATION - {original_entry.label}",
            lines=cancellation_lines,
            piece_number=f"ANNUL-{original_entry.piece_number or original_entry.entry_number}",
            source="cancellation",
            source_id=original_entry.id,
            created_by=cancelled_by,
        )
        
        # Marquer l'originale comme annulée
        original_entry.status = "cancelled"
        
        self.db.commit()
        
        # Log d'audit
        AuditLog.log(
            db_session=self.db,
            action_type="CANCEL",
            entity_type="AccountingEntry",
            entity_id=original_entry.id,
            entity_label=f"Écriture {original_entry.entry_number}",
            new_values={
                "status": "cancelled",
                "cancellation_entry_id": cancellation_entry.id,
                "reason": cancellation_reason,
            },
            user_login=cancelled_by,
        )
        
        return cancellation_entry

    def delete_entry(self, entry_id: int, deleted_by: Optional[str] = None) -> bool:
        """
        Supprime une écriture (seulement si brouillon)
        
        Args:
            entry_id : ID de l'écriture
            deleted_by : Utilisateur suppresseur
            
        Returns:
            bool : True si supprimé
            
        Raises:
            JournalEntryError : Si l'écriture n'est pas en brouillon
        """
        entry = self.get_entry(entry_id)
        
        if not entry:
            raise JournalEntryError(f"L'écriture {entry_id} n'existe pas")
        
        if not entry.is_draft:
            raise JournalEntryError(
                f"Impossible de supprimer une écriture {entry.status}. "
                f"Seules les écritures en brouillon peuvent être supprimées."
            )
        
        # Log d'audit avant suppression
        AuditLog.log(
            db_session=self.db,
            action_type="DELETE",
            entity_type="AccountingEntry",
            entity_id=entry.id,
            entity_label=f"Écriture {entry.entry_number}",
            old_values={
                "label": entry.label,
                "total_debit": str(entry.total_debit),
                "lines_count": len(entry.lines),
            },
            user_login=deleted_by,
        )
        
        self.db.delete(entry)
        self.db.commit()
        
        return True

    def list_entries(
        self,
        dossier_id: int,
        fiscal_year_id: Optional[int] = None,
        journal_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        account_number: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[AccountingEntry], int]:
        """
        Liste les écritures avec filtres
        
        Returns:
            Tuple[List[AccountingEntry], int] : (écritures, total)
        """
        query = self.db.query(AccountingEntry).options(
            joinedload(AccountingEntry.lines),
            joinedload(AccountingEntry.journal),
        ).filter(AccountingEntry.dossier_id == dossier_id)
        
        if fiscal_year_id:
            query = query.filter(AccountingEntry.fiscal_year_id == fiscal_year_id)
        
        if journal_id:
            query = query.filter(AccountingEntry.journal_id == journal_id)
        
        if status:
            query = query.filter(AccountingEntry.status == status)
        
        if date_from:
            query = query.filter(AccountingEntry.entry_date >= date_from)
        
        if date_to:
            query = query.filter(AccountingEntry.entry_date <= date_to)
        
        if account_number:
            # Filtrer par compte via les lignes
            query = query.join(AccountingEntryLine).filter(
                AccountingEntryLine.account_number.like(f"{account_number}%")
            )
        
        total = query.count()
        entries = query.order_by(
            AccountingEntry.entry_date.desc(),
            AccountingEntry.entry_number.desc(),
        ).offset(offset).limit(limit).all()
        
        return entries, total
