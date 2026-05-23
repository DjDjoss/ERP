# -*- coding: utf-8 -*-
"""
Factories pour le module Finance

Utilisation avec factory_boy pour générer des données de test réalistes
"""

import random
from datetime import date, timedelta
from decimal import Decimal
import factory
from factory import Faker, Sequence, SubFactory, LazyAttribute, LazyFunction
from factory.alchemy import SQLAlchemyModelFactory

from backend.connection_manager import Base
from finance.models.core import FiscalYear, AccountingJournal, AccountingAccount
from finance.models.entries import AccountingEntry, AccountingEntryLine
from finance.models.treasury import BankAccount, BankTransaction, BankReconciliation


class FiscalYearFactory(SQLAlchemyModelFactory):
    """Factory pour créer des exercices comptables"""
    
    class Meta:
        model = FiscalYear
        sqlalchemy_session = None  # Sera défini dans les tests
    
    dossier_id = Sequence(lambda n: n % 5 + 1)  # 5 dossiers max
    label = Sequence(lambda n: f"Exercice {2020 + n}")
    start_date = LazyFunction(lambda: date(2020, 1, 1))
    end_date = LazyAttribute(lambda obj: obj.start_date.replace(year=obj.start_date.year + 11, day=31, month=12))
    status = "open"
    is_closing_locked = False


class AccountingJournalFactory(SQLAlchemyModelFactory):
    """Factory pour créer des journaux comptables"""
    
    class Meta:
        model = AccountingJournal
        sqlalchemy_session = None
    
    dossier_id = Sequence(lambda n: n % 5 + 1)
    fiscal_year_id = None
    code = Sequence(lambda n: f"J{str(n).zfill(3)}")
    label = Sequence(lambda n: f"Journal {n}")
    journal_type = "general"
    is_active = True
    last_entry_number = 0
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = cls._meta.sqlalchemy_session
        if kwargs.get('fiscal_year_id') is None:
            # Créer un exercice par défaut
            fiscal_year = FiscalYearFactory()
            session.add(fiscal_year)
            session.commit()
            kwargs['fiscal_year_id'] = fiscal_year.id
        return super()._create(model_class, *args, **kwargs)


class AccountingAccountFactory(SQLAlchemyModelFactory):
    """Factory pour créer des comptes comptables"""
    
    class Meta:
        model = AccountingAccount
        sqlalchemy_session = None
    
    dossier_id = Sequence(lambda n: n % 5 + 1)
    number = Sequence(lambda n: f"{random.choice(['10', '41', '40', '51', '60', '70'])}{str(n).zfill(6)}")
    label = Sequence(lambda n: f"Compte {n}")
    account_class = "7"
    account_type = "general"
    is_active = True
    is_third_party = False
    third_party_code = None
    parent_id = None
    
    class Params:
        # Presets pour types courants
        customer = factory.Trait(
            number=Sequence(lambda n: f"411{str(n).zfill(5)}"),
            account_type="third_party_customer",
            is_third_party=True,
            label=Sequence(lambda n: f"Client {n}"),
        )
        supplier = factory.Trait(
            number=Sequence(lambda n: f"401{str(n).zfill(5)}"),
            account_type="third_party_supplier",
            is_third_party=True,
            label=Sequence(lambda n: f"Fournisseur {n}"),
        )
        bank = factory.Trait(
            number=Sequence(lambda n: f"512{str(n).zfill(5)}"),
            account_type="bank",
            label=Sequence(lambda n: f"Banque {n}"),
        )
        tax = factory.Trait(
            number=Sequence(lambda n: f"445{str(n).zfill(5)}"),
            account_type="tax",
            label=Sequence(lambda n: f"TVA {n}"),
        )
        expense = factory.Trait(
            number=Sequence(lambda n: f"6{str(n).zfill(6)}"),
            account_class="6",
            label=Sequence(lambda n: f"Charge {n}"),
        )
        income = factory.Trait(
            number=Sequence(lambda n: f"7{str(n).zfill(6)}"),
            account_class="7",
            label=Sequence(lambda n: f"Produit {n}"),
        )


class AccountingEntryFactory(SQLAlchemyModelFactory):
    """Factory pour créer des écritures comptables"""
    
    class Meta:
        model = AccountingEntry
        sqlalchemy_session = None
    
    dossier_id = Sequence(lambda n: n % 5 + 1)
    fiscal_year_id = None
    journal_id = None
    entry_number = Sequence(lambda n: n)
    piece_number = Sequence(lambda n: f"PC-{str(n).zfill(5)}")
    label = Sequence(lambda n: f"Écriture {n}")
    entry_date = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 365)))
    document_date = None
    period_date = None
    source = "manual"
    source_id = None
    status = "draft"
    is_system = False
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    created_by = "test_user"
    validated_by = None
    validated_at = None
    
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        session = cls._meta.sqlalchemy_session
        
        # Créer fiscal_year et journal si non fournis
        if kwargs.get('fiscal_year_id') is None:
            fiscal_year = FiscalYearFactory()
            session.add(fiscal_year)
            session.commit()
            kwargs['fiscal_year_id'] = fiscal_year.id
        
        if kwargs.get('journal_id') is None:
            journal = AccountingJournalFactory(fiscal_year_id=kwargs['fiscal_year_id'])
            session.add(journal)
            session.commit()
            kwargs['journal_id'] = journal.id
        
        entry = super()._create(model_class, *args, **kwargs)
        
        # Recalculer les totaux depuis les lignes si elles existent
        if hasattr(entry, 'lines') and entry.lines:
            entry.recalculate_totals()
            session.commit()
        
        return entry


class AccountingEntryLineFactory(SQLAlchemyModelFactory):
    """Factory pour créer des lignes d'écriture"""
    
    class Meta:
        model = AccountingEntryLine
        sqlalchemy_session = None
    
    entry_id = None
    line_number = Sequence(lambda n: n)
    account_id = None
    account_number = Sequence(lambda n: f"706{str(n).zfill(5)}")
    account_label = "Prestation de services"
    third_party_code = None
    third_party_name = None
    debit = Decimal("0.00")
    credit = Decimal("0.00")
    vat_code = None
    vat_rate = None
    vat_amount = None
    lettering_code = None
    lettering_date = None
    analytic_axis = None
    analytic_section = None
    label = None
    bank_reconciliation_id = None
    is_reconciled = False
    
    class Params:
        # Ligne de débit
        debit_line = factory.Trait(
            debit=Decimal("1000.00"),
            credit=Decimal("0.00"),
        )
        # Ligne de crédit
        credit_line = factory.Trait(
            debit=Decimal("0.00"),
            credit=Decimal("1000.00"),
        )


class BankAccountFactory(SQLAlchemyModelFactory):
    """Factory pour créer des comptes bancaires"""
    
    class Meta:
        model = BankAccount
        sqlalchemy_session = None
    
    dossier_id = Sequence(lambda n: n % 5 + 1)
    account_number = Sequence(lambda n: f"FR76{n % 100:02d}99{str(n).zfill(10)}")
    bank_code = "99999"
    branch_code = "99999"
    rib_key = "99"
    bic_swift = "BDFEFRPP"
    accounting_account_id = None
    currency = "EUR"
    label = Sequence(lambda n: f"Compte Bancaire {n}")
    is_active = True
    last_statement_balance = Decimal("0.00")
    last_statement_date = None


class BankTransactionFactory(SQLAlchemyModelFactory):
    """Factory pour créer des transactions bancaires"""
    
    class Meta:
        model = BankTransaction
        sqlalchemy_session = None
    
    bank_account_id = None
    dossier_id = Sequence(lambda n: n % 5 + 1)
    transaction_date = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 90)))
    value_date = None
    booking_date = None
    amount = LazyFunction(lambda: Decimal(str(random.uniform(-5000, 5000))).quantize(Decimal("0.01")))
    balance_after = None
    label = Sequence(lambda n: f"Transaction {n}")
    counterparty_name = Faker("company")
    counterparty_iban = None
    reference = None
    additional_info = None
    is_reconciled = False
    reconciliation_id = None
    suggested_account_id = None
    matched_entry_line_ids = None
    import_source = "CSV"
    import_batch_id = None


class BankReconciliationFactory(SQLAlchemyModelFactory):
    """Factory pour créer des rapprochements bancaires"""
    
    class Meta:
        model = BankReconciliation
        sqlalchemy_session = None
    
    bank_account_id = None
    statement_number = Sequence(lambda n: f"REL-{str(n).zfill(5)}")
    statement_date = LazyFunction(lambda: date.today() - timedelta(days=random.randint(0, 30)))
    period_start = LazyAttribute(lambda obj: obj.statement_date.replace(day=1))
    period_end = LazyAttribute(lambda obj: obj.statement_date)
    start_balance = Decimal("0.00")
    end_balance = Decimal("0.00")
    reconciled_balance = None
    total_transactions = 0
    total_reconciled_transactions = 0
    total_unreconciled_transactions = 0
    difference = None
    status = "in_progress"
    is_completed = False
    is_locked = False
    reconciled_by = None
    reconciled_at = None
