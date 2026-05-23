# 📋 TODOO - TÂCHES RESTANTES DJOSS-ERP

**Dernière mise à jour** : 2025
**Module en cours** : Finance (Phase 2 - Priorité CRITIQUE)

---

## 🔴 PRIORITÉ 1 : FINALISER MODULE FINANCE

### API REST (FastAPI)
- [ ] **finance/api/schemas.py** - Créer les schémas Pydantic
  - [ ] FiscalYearSchema (create, update, response)
  - [ ] AccountingJournalSchema
  - [ ] AccountingAccountSchema
  - [ ] AccountingEntrySchema (avec lignes imbriquées)
  - [ ] AccountingEntryLineSchema
  - [ ] BankAccountSchema
  - [ ] BankTransactionSchema
  - [ ] TrialBalanceSchema
  - [ ] GeneralLedgerSchema

- [ ] **finance/api/routes.py** - Créer les endpoints REST
  - [ ] `POST /api/fiscal-years/` - Créer exercice
  - [ ] `GET /api/fiscal-years/` - Lister exercices
  - [ ] `GET /api/fiscal-years/{id}` - Détail exercice
  - [ ] `PUT /api/fiscal-years/{id}` - Modifier exercice
  - [ ] `POST /api/journals/` - Créer journal
  - [ ] `GET /api/journals/` - Lister journaux
  - [ ] `POST /api/accounts/` - Créer compte
  - [ ] `GET /api/accounts/` - Lister comptes (PCG)
  - [ ] `POST /api/entries/` - Créer écriture
  - [ ] `GET /api/entries/` - Lister écritures (filtres)
  - [ ] `GET /api/entries/{id}` - Détail écriture
  - [ ] `PUT /api/entries/{id}` - Modifier écriture
  - [ ] `POST /api/entries/{id}/validate` - Valider écriture
  - [ ] `POST /api/entries/{id}/cancel` - Annuler écriture
  - [ ] `DELETE /api/entries/{id}` - Supprimer écriture
  - [ ] `GET /api/reports/trial-balance/` - Balance
  - [ ] `GET /api/reports/general-ledger/` - Grand Livre
  - [ ] `GET /api/reports/income-statement/` - Compte de résultat
  - [ ] `POST /api/pcg/import/` - Importer PCG
  - [ ] `POST /api/lettering/auto/` - Lettrage auto
  - [ ] `POST /api/lettering/manual/` - Lettrage manuel
  - [ ] `GET /api/bank/suggestions/` - Suggestions rapprochement
  - [ ] `POST /api/bank/reconcile/` - Rapprocher transaction

- [ ] **finance/api/__init__.py** - Initialisation module API

### Tests Complémentaires
- [ ] **finance/tests/test_pcg_loader.py**
  - [ ] Test import fichier PCG
  - [ ] Test création journaux standards
  - [ ] Test résumé PCG

- [ ] **finance/tests/test_financial_reports.py**
  - [ ] Test balance générale
  - [ ] Test grand livre
  - [ ] Test compte de résultat

- [ ] **finance/tests/test_lettering.py**
  - [ ] Test lettrage automatique
  - [ ] Test lettrage manuel
  - [ ] Test détection non-lettrés

- [ ] **finance/tests/test_bank_reconciliation.py**
  - [ ] Test suggestions
  - [ ] Test rapprochement
  - [ ] Test complétion

- [ ] **finance/factories/factories.py** - Factory Boy
  - [ ] FiscalYearFactory
  - [ ] AccountingJournalFactory
  - [ ] AccountingAccountFactory
  - [ ] AccountingEntryFactory
  - [ ] AccountingEntryLineFactory
  - [ ] BankAccountFactory
  - [ ] BankTransactionFactory

### Intégration Backend
- [ ] **backend/main.py** - Inclure routes finance
  ```python
  from finance.api.routes import router as finance_router
  app.include_router(finance_router, prefix="/api/finance", tags=["Finance"])
  ```

- [ ] **Migrations Alembic**
  - [ ] Configurer Alembic pour le projet
  - [ ] Générer migration initiale pour tables finance
  - [ ] Tester migration sur PostgreSQL

### Documentation API
- [ ] Swagger/OpenAPI - Vérifier que tous les endpoints sont documentés
- [ ] Exemples de requêtes/réponses dans les docstrings

---

## 🟠 PRIORITÉ 2 : FRONTEND PY SIDE6

### Refonte UI Comptabilité
- [ ] **modules/accounting/views.py** - Nouvelle interface à onglets
  - [ ] Onglet "Tableau de bord" - Dashboard 2026
  - [ ] Onglet "Exercices" - Gestion fiscal years
  - [ ] Onglet "Journaux" - Liste + création
  - [ ] Onglet "Plan Comptable" - Arborescence PCG
  - [ ] Onglet "Écritures" - Saisie + liste + filtres
  - [ ] Onglet "Rapports" - Balance, Grand Livre, etc.
  - [ ] Onglet "Tiers" - Lettrage clients/fournisseurs
  - [ ] Onglet "Banque" - Rapprochement

- [ ] **modules/accounting/dialogs/** - Nouvelles fenêtres
  - [ ] fiscal_year_dialog.py - Créer/modifier exercice
  - [ ] journal_dialog.py - Créer/modifier journal
  - [ ] account_dialog.py - Fiche compte
  - [ ] entry_dialog.py - Saisie écriture (avec grille débit/crédit)
  - [ ] entry_validation_dialog.py - Validation multi-écritures
  - [ ] trial_balance_window.py - Affichage balance
  - [ ] general_ledger_window.py - Affichage grand livre
  - [ ] lettering_window.py - Interface lettrage
  - [ ] bank_reconciliation_window.py - Rapprochement bancaire

- [ ] **Modules existants à migrer**
  - [ ] pcg_list.py → Utiliser nouveau service PCGLoaderService
  - [ ] ecriture_saisie.py → Utiliser JournalEntryService
  - [ ] accounting_reports.py → Utiliser FinancialReportsService
  - [ ] dossier_manager.py → Intégrer avec FiscalYear

### Connexion API
- [ ] **modules/api_client.py** - Client HTTP pour FastAPI
  - [ ] GET/POST/PUT/DELETE wrappers
  - [ ] Gestion authentification JWT
  - [ ] Gestion erreurs API
  - [ ] Timeout et retry

---

## 🟡 PRIORITÉ 3 : MODULE CORE (PRÉREQUIS)

### Multi-Tenancy
- [ ] **core/models/company.py**
  - [ ] Company (Société)
  - [ ] Branch (Établissement/Succursale)

- [ ] **core/models/user.py**
  - [ ] Custom User Model
  - [ ] RBAC (Rôles et permissions)

- [ ] **core/models/audit.py**
  - [ ] AuditLog global (transverse)

### Authentification
- [ ] **core/api/auth.py**
  - [ ] Login/Logout
  - [ ] JWT tokens
  - [ ] Refresh tokens
  - [ ] Password reset

---

## 🟢 PRIORITÉ 4 : AUTRES MODULES MÉTIER

### Module Ventes (sales/) - Phase 3
- [ ] models/
  - [ ] Customer
  - [ ] Quotation
  - [ ] SaleOrder
  - [ ] Invoice
  - [ ] Payment
- [ ] services/
  - [ ] invoice_service.py (génère écritures auto)
  - [ ] payment_service.py
- [ ] api/
- [ ] tests/

### Module Achats (purchases/) - Phase 4
- [ ] models/
  - [ ] Supplier
  - [ ] PurchaseOrder
  - [ ] Bill
  - [ ] Payment
- [ ] services/
  - [ ] bill_service.py (génère écritures auto)
- [ ] api/
- [ ] tests/

### Module Stock (inventory/) - Phase 5
- [ ] models/
  - [ ] Product
  - [ ] Warehouse
  - [ ] StockMove
  - [ ] InventoryAdjustment
- [ ] services/
  - [ ] valuation_service.py (génère écritures auto)
- [ ] api/
- [ ] tests/

### Module RH (hr/) - Phase 6
- [ ] models/
  - [ ] Employee
  - [ ] Contract
  - [ ] Payslip
  - [ ] Leave
- [ ] services/
  - [ ] payroll_service.py (génère écritures auto)
- [ ] api/
- [ ] tests/

---

## 🔵 PRIORITÉ 5 : INFRASTRUCTURE & DEVOPS

### Docker
- [ ] **Dockerfile** - Image backend Python
- [ ] **docker-compose.yml**
  - [ ] Service postgres
  - [ ] Service backend
  - [ ] Service redis (cache/queue)
  - [ ] service celery (tasks async)
  - [ ] service flower (monitoring celery)

### CI/CD
- [ ] **.github/workflows/ci.yml**
  - [ ] Lint (black, flake8, pylint)
  - [ ] Tests (pytest avec coverage)
  - [ ] Build Docker
  - [ ] Déploiement staging

### Monitoring
- [ ] **config/logging.py** - Configuration logging
- [ ] Intégration Sentry (erreurs production)
- [ ] Prometheus metrics (performance)

---

## 📊 ROADMAP GLOBALE

| Phase | Module | Statut | Priorité | Jours estimés |
|-------|--------|--------|----------|---------------|
| 0 | Infrastructure | ✅ Partiel | CRITIQUE | - |
| 1 | Core | ⏳ À faire | CRITIQUE | 5-7 |
| 2 | Finance | 🔵 60% fait | CRITIQUE | 10-15 |
| 3 | Sales | ⚪ Non commencé | HAUTE | 7-10 |
| 4 | Purchases | ⚪ Non commencé | HAUTE | 5-7 |
| 5 | Inventory | ⚪ Non commencé | HAUTE | 7-10 |
| 6 | HR | ⚪ Non commencé | MOYENNE | 10-14 |
| 7 | Productivity | ⚪ Non commencé | MOYENNE | 3-5 |
| 8 | CRM | ⚪ Non commencé | MOYENNE | 5-7 |
| 9 | Projects | ⚪ Non commencé | MOYENNE | 7-10 |
| 10 | Reporting/BI | ⚪ Non commencé | BASSE | 10-15 |

**Total estimé** : ~70-100 jours de développement

---

## 🎯 PROCHAINES ACTIONS IMMÉDIATES

1. [ ] Compléter l'API REST du module Finance (schemas + routes)
2. [ ] Écrire tous les tests unitaires restants
3. [ ] Configurer Alembic pour migrations
4. [ ] Tester avec PostgreSQL en local
5. [ ] Commencer refonte frontend PySide6 (onglets)
6. [ ] Documenter API avec Swagger

---

## 📞 SUPPORT & QUESTIONS

Pour toute question sur l'architecture ou l'implémentation :
- Consulter `README_Coding_Projet.md` pour les principes directeurs
- Vérifier les docstrings dans les services
- Examiner les tests pour comprendre l'usage attendu

---

**Note** : Ce fichier sera mis à jour régulièrement au fur et à mesure de l'avancement du projet.
