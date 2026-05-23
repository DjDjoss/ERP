# -*- coding: utf-8 -*-
"""
Modèles du module Finance - Refactorisé

Architecture Django-like avec SQLAlchemy :
- models/ : Modèles de données
- services/ : Logique métier
- api/ : Endpoints REST
- tests/ : Tests unitaires et d'intégration
- factories/ : Données de test

Ordre d'import important pour les dépendances entre modèles
"""

from finance.models.core import (
    FiscalYear,
    AccountingJournal,
    AccountingAccount,
    AnalyticSection,
    AnalyticAxis,
)

from finance.models.entries import (
    AccountingEntry,
    AccountingEntryLine,
)

from finance.models.treasury import (
    BankAccount,
    BankTransaction,
    BankReconciliation,
    CashBox,
)

from finance.models.reports import (
    TrialBalance,
    GeneralLedger,
    BalanceSheet,
    IncomeStatement,
    VATDeclaration,
)

from finance.models.assets import (
    Asset,
    AssetDepreciation,
)

from finance.models.audit import AuditLog

__all__ = [
    # Core
    "FiscalYear",
    "AccountingJournal",
    "AccountingAccount",
    "AnalyticSection",
    "AnalyticAxis",
    # Entries
    "AccountingEntry",
    "AccountingEntryLine",
    # Treasury
    "BankAccount",
    "BankTransaction",
    "BankReconciliation",
    "CashBox",
    # Reports
    "TrialBalance",
    "GeneralLedger",
    "BalanceSheet",
    "IncomeStatement",
    "VATDeclaration",
    # Assets
    "Asset",
    "AssetDepreciation",
    # Audit
    "AuditLog",
]
