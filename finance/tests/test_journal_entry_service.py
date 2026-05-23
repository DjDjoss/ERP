# -*- coding: utf-8 -*-
"""
Tests unitaires pour le service JournalEntryService
"""

import pytest
from datetime import date
from decimal import Decimal
from finance.models.core import FiscalYear, AccountingJournal, AccountingAccount
from finance.services.journal_entry_service import JournalEntryService, JournalEntryError


class TestJournalEntryService:
    """Tests pour le service d'écritures comptables"""

    @pytest.fixture
    def setup_data(self, db_session, sample_dossier_id):
        """Prépare les données de base pour les tests"""
        # Créer un exercice
        fiscal_year = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Exercice 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="open",
        )
        db_session.add(fiscal_year)
        db_session.flush()
        
        # Créer un journal
        journal = AccountingJournal(
            dossier_id=sample_dossier_id,
            code="OD",
            label="Opérations diverses",
            journal_type="general",
        )
        db_session.add(journal)
        db_session.flush()
        
        # Créer des comptes
        account_512 = AccountingAccount(
            dossier_id=sample_dossier_id,
            number="512000",
            label="Banque",
            account_class="5",
            account_type="bank",
        )
        account_706 = AccountingAccount(
            dossier_id=sample_dossier_id,
            number="706000",
            label="Prestations de services",
            account_class="7",
        )
        account_4457 = AccountingAccount(
            dossier_id=sample_dossier_id,
            number="445700",
            label="TVA collectée",
            account_class="4",
        )
        
        for acc in [account_512, account_706, account_4457]:
            db_session.add(acc)
        
        db_session.commit()
        
        return {
            'fiscal_year_id': fiscal_year.id,
            'journal_id': journal.id,
            'account_512_id': account_512.id,
            'account_706_id': account_706.id,
            'account_4457_id': account_4457.id,
        }

    def test_create_balanced_entry(self, db_session, sample_dossier_id, setup_data):
        """Test de création d'une écriture équilibrée"""
        service = JournalEntryService(db_session)
        
        lines = [
            {'account_id': setup_data['account_512_id'], 'debit': 1200, 'credit': 0},
            {'account_id': setup_data['account_706_id'], 'debit': 0, 'credit': 1000},
            {'account_id': setup_data['account_4457_id'], 'debit': 0, 'credit': 200},
        ]
        
        entry = service.create_entry(
            dossier_id=sample_dossier_id,
            fiscal_year_id=setup_data['fiscal_year_id'],
            journal_id=setup_data['journal_id'],
            entry_date=date(2025, 6, 15),
            label="Facture de prestation",
            lines=lines,
            piece_number="FAC-2025-001",
        )
        
        assert entry.id is not None
        assert entry.entry_number == 1
        assert entry.total_debit == Decimal('1200.00')
        assert entry.total_credit == Decimal('1200.00')
        assert entry.is_balanced
        assert entry.status == 'draft'

    def test_create_unbalanced_entry_raises_error(self, db_session, sample_dossier_id, setup_data):
        """Test que la création d'une écriture déséquilibrée lève une erreur"""
        service = JournalEntryService(db_session)
        
        lines = [
            {'account_id': setup_data['account_512_id'], 'debit': 1000, 'credit': 0},
            {'account_id': setup_data['account_706_id'], 'debit': 0, 'credit': 900},  # Déséquilibré
        ]
        
        with pytest.raises(JournalEntryError) as exc_info:
            service.create_entry(
                dossier_id=sample_dossier_id,
                fiscal_year_id=setup_data['fiscal_year_id'],
                journal_id=setup_data['journal_id'],
                entry_date=date(2025, 6, 15),
                label="Écriture déséquilibrée",
                lines=lines,
            )
        
        assert "déséquilibrée" in str(exc_info.value)

    def test_validate_entry(self, db_session, sample_dossier_id, setup_data):
        """Test de validation d'une écriture"""
        service = JournalEntryService(db_session)
        
        # Créer une écriture
        lines = [
            {'account_id': setup_data['account_512_id'], 'debit': 500, 'credit': 0},
            {'account_id': setup_data['account_706_id'], 'debit': 0, 'credit': 500},
        ]
        
        entry = service.create_entry(
            dossier_id=sample_dossier_id,
            fiscal_year_id=setup_data['fiscal_year_id'],
            journal_id=setup_data['journal_id'],
            entry_date=date(2025, 6, 15),
            label="Test validation",
            lines=lines,
        )
        
        # Valider
        validated_entry = service.validate_entry(entry.id, validated_by="test_user")
        
        assert validated_entry.status == 'posted'
        assert validated_entry.validated_by == "test_user"
        assert validated_entry.is_posted is True

    def test_cannot_validate_closed_fiscal_year(self, db_session, sample_dossier_id):
        """Test qu'on ne peut pas créer dans un exercice fermé"""
        # Créer un exercice fermé
        fiscal_year = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Exercice 2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="closed",
        )
        db_session.add(fiscal_year)
        db_session.flush()
        
        service = JournalEntryService(db_session)
        
        with pytest.raises(JournalEntryError) as exc_info:
            service.create_entry(
                dossier_id=sample_dossier_id,
                fiscal_year_id=fiscal_year.id,
                journal_id=1,
                entry_date=date(2024, 6, 15),
                label="Dans exercice fermé",
                lines=[],
            )
        
        assert "fermé" in str(exc_info.value).lower() or "exercice" in str(exc_info.value).lower()
