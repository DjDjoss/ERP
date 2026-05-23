# 🚀 GUIDE DE CODAGE PROJET DJOSS-ERP

> **Philosophie** : "Finance-First, Test-Driven, Modular Growth"  
> Ce document décrit la méthodologie stricte pour développer Djoss-ERP module par module, en garantissant stabilité, évolutivité et qualité.

---

## 📋 SOMMAIRE

1. [Principes Fondamentaux](#1-principes-fondamentaux)
2. [Architecture Technique de Base](#2-architecture-technique-de-base)
3. [Ordre de Développement des Modules](#3-ordre-de-développement-des-modules)
4. [Workflow de Développement par Module](#4-workflow-de-développement-par-module)
5. [Stratégie de Tests Obligatoire](#5-stratégie-de-tests-obligatoire)
6. [Checklist de Validation par Module](#6-checklist-de-validation-par-module)
7. [Bonnes Pratiques de Code](#7-bonnes-pratiques-de-code)
8. [Gestion des Dépendances entre Modules](#8-gestion-des-dépendances-entre-modules)
9. [Commandes Utiles](#9-commandes-utiles)
10. [Dépannage & FAQ](#10-dépannage--faq)

---

## 1. PRINCIPES FONDAMENTAUX

### 🎯 Règle d'Or #1 : Finance-First
La comptabilité est le **cœur battant** de l'ERP. Tout module métier (Vente, Achat, Stock, RH, etc.) doit pouvoir générer des écritures comptables automatiques.

**Conséquence** : Le module `finance` doit être codé, testé et validé **avant** tout module métier.

### 🧪 Règle d'Or #2 : Test-Driven Development (TDD)
Aucune fonctionnalité n'est considérée comme terminée sans ses tests unitaires et d'intégration.

**Exigence** : Couverture de code minimale de **90%** pour les modules critiques (Finance, Core).

### 🔗 Règle d'Or #3 : Couplage Faible, Cohésion Forte
Chaque module doit être autonome et communiquer via des APIs internes bien définies. Éviter les imports circulaires.

### 📦 Règle d'Or #4 : Multi-Tenancy Natif
Dès le premier modèle, intégrer `company` et `branch` comme foreign keys obligatoires (sauf exceptions Core).

---

## 2. ARCHITECTURE TECHNIQUE DE BASE

### Stack Technologique
```
Backend:    Django 5.x + Django REST Framework 3.15+
Database:   PostgreSQL 16+ (avec extensions: hstore, pgcrypto)
Cache/Queue: Redis 7+ (pour Celery et caching)
Async Tasks: Celery 5.3+ avec Flower pour monitoring
API Doc:    drf-spectacular (OpenAPI 3.0 / Swagger)
Auth:       djangorestframework-simplejwt + django-allauth
Testing:    pytest-django + factory_boy + coverage
DevOps:     Docker + Docker Compose + GitHub Actions
```

### Structure du Projet
```
djosserp/
├── core/                   # Applications socles (obligatoires en premier)
│   ├── apps.py
│   ├── models/
│   │   ├── company.py      # Company, Branch
│   │   ├── user.py         # Custom User Model
│   │   ├── audit.py        # AuditLog
│   │   └── ...
│   ├── permissions.py
│   └── signals.py
│
├── finance/                # MODULE PRIORITAIRE #1
│   ├── models/
│   │   ├── accounting.py   # PlanComptable, EcritureComptable, Exercice
│   │   ├── treasury.py     # Bank, Transaction, Rapprochement
│   │   ├── assets.py       # Immobilisations
│   │   └── tax.py          # Taxes, TVA
│   ├── services/           # Logique métier complexe
│   │   ├── journal_entry.py
│   │   └── financial_reports.py
│   ├── api/
│   └── tests/
│
├── sales/                  # MODULE #2 (dépend de finance)
├── purchases/              # MODULE #3 (dépend de finance)
├── inventory/              # MODULE #4 (dépend de purchases/sales)
├── hr/                     # MODULE #5
├── productivity/           # MODULE #6 (transverse)
├── crm/                    # MODULE #7
├── projects/               # MODULE #8
│
├── config/                 # Configuration Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── prod.py
│   │   └── test.py
│   ├── urls.py
│   └── celery.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── .pre-commit-config.yaml
└── README_Coding_Projet.md (CE FICHIER)
```

---

## 3. ORDRE DE DÉVELOPPEMENT DES MODULES

Respecter strictement cet ordre pour éviter les refactoring coûteux :

| Phase | Module | Priorité | Durée Est. | Dépendances | Critère de Fin |
|-------|--------|----------|------------|-------------|----------------|
| **0** | **Infrastructure** | CRITIQUE |  | Aucune | Docker OK, CI/CD OK, DB up |
| **1** | **Core** | CRITIQUE |  | Infrastructure | Auth, RBAC, Multi-tenancy fonctionnels |
| **2** | **Finance** | CRITIQUE |  | Core | Écritures validées, États financiers OK |
| **3** | **Sales** | HAUTE |  | Core, Finance | Devis → Facture → Écriture auto |
| **4** | **Purchases** | HAUTE |  | Core, Finance | Bon de commande → Facture fournisseur → Écriture |
| **5** | **Inventory** | HAUTE |  | Sales, Purchases | Mouvements de stock valorisés → Écritures |
| **6** | **HR** | MOYENNE |  | Core, Finance | Paie → Écritures de salaire |
| **7** | **Productivity** | MOYENNE |  | Core | Notifications, Tâches, Calendrier |
| **8** | **CRM** | MOYENNE |  | Core, Sales | Pipeline → Opportunités |
| **9** | **Projects** | MOYENNE |  | Core, Finance, HR | Suivi temps/coût → Facturation |
| **10**| **Reporting/BI** | BASSE |  | Tous modules | Dashboards, exports |

> ⚠️ **INTERDICTION FORMELLE** : Ne pas commencer un module N+1 tant que le module N n'a pas passé tous les tests et la checklist de validation.

---

## 4. WORKFLOW DE DÉVELOPPEMENT PAR MODULE

Pour **CHAQUE** nouveau module, suivre scrupuleusement ces 7 étapes :

### Étape 1 : Initialisation du Module
```bash
# Créer l'application Django
python manage.py startapp <module_name>

# Structure interne à créer manuellement
mkdir -p <module_name>/{models,services,api,tests,templates,static}
touch <module_name>/models/__init__.py
touch <module_name>/services/__init__.py
touch <module_name>/api/__init__.py
```

### Étape 2 : Spécification des Modèles de Données
- Lire le cahier des charges section correspondante
- Définir tous les modèles dans `models/`
- Ajouter `company` et `branch` FK partout (sauf exception)
- Définir les indexes, constraints, unique_together
- Créer les migrations initiales

```bash
python manage.py makemigrations <module_name>
python manage.py sqlmigrate <module_name> 0001_initial  # Vérifier le SQL
```

### Étape 3 : Implémentation de la Logique Métier (Services)
- **Jamais** de logique métier complexe dans les vues ou serializers
- Utiliser le pattern `services/` pour encapsuler la logique
- Exemple : `finance/services/journal_entry.py` pour créer une écriture comptable

```python
# <module_name>/services/example.py
from decimal import Decimal
from django.db import transaction

@transaction.atomic
def create_accounting_entry(data):
    """
    Crée une écriture comptable avec validation automatique.
    Retourne l'écriture ou lève une exception.
    """
    # 1. Vérifications métier (partie double, soldes, etc.)
    # 2. Création des lignes d'écriture
    # 3. Validation si critères remplis
    # 4. Génération signal pour notifications
    pass
```

### Étape 4 : API REST (Serializers & ViewSets)
- Serializers avec validation stricte
- ViewSets avec permissions RBAC
- Pagination, filtering, ordering activés par défaut
- Documentation automatique (Swagger)

```python
# <module_name>/api/serializers.py
# <module_name>/api/viewsets.py
# <module_name>/api/urls.py
```

### Étape 5 : Tests Unitaires et d'Intégration
**OBLIGATOIRE AVANT DE PASSER À LA SUITE**

Créer les tests dans `<module_name>/tests/` :
- `test_models.py` : Tests de création, contraintes, méthodes
- `test_services.py` : Tests de logique métier (cas nominaux + cas d'erreur)
- `test_api.py` : Tests des endpoints (auth, permissions, CRUD, validations)
- `test_integration.py` : Tests de bout en bout avec autres modules

```bash
# Lancer les tests du module
pytest <module_name>/tests/ -v --cov=<module_name> --cov-report=html

# Exigence : Coverage > 90% pour modules critiques, > 80% pour autres
```

### Étape 6 : Documentation et Seeds
- Mettre à jour la documentation API (auto-générée mais vérifier les descriptions)
- Créer des fixtures de démo (`fixtures/demo_<module>.json`)
- Rédiger un README spécifique au module dans `<module_name>/README.md`

### Étape 7 : Validation et Merge
- Passer la [Checklist de Validation](#6-checklist-de-validation-par-module)
- Revue de code par un pair (minimum 1 approve)
- Merge sur `develop` après succès du pipeline CI/CD

---

## 5. STRATÉGIE DE TESTS OBLIGATOIRE

### Types de Tests Requis

#### 5.1 Tests Unitaires (Unit Tests)
Testent une fonction/méthode isolée.

```python
# finance/tests/test_services.py
def test_journal_entry_balanced():
    """Une écriture doit être équilibrée (débit = crédit)"""
    entry = create_test_journal_entry(debit=1000, credit=1000)
    assert entry.is_balanced() is True

def test_journal_entry_unbalanced_raises_error():
    """Une écriture déséquilibrée doit lever une exception"""
    with pytest.raises(ValidationError):
        create_test_journal_entry(debit=1000, credit=900)
```

#### 5.2 Tests d'Intégration (Integration Tests)
Testent l'interaction entre plusieurs composants/modules.

```python
# sales/tests/test_integration_with_finance.py
def test_invoice_creation_generates_accounting_entry():
    """La validation d'une facture doit générer une écriture comptable"""
    invoice = create_draft_invoice()
    invoice.validate()
    
    assert AccountingEntry.objects.filter(
        source_type='Invoice',
        source_id=invoice.id
    ).exists()
    
    entry = AccountingEntry.objects.get(source_id=invoice.id)
    assert entry.debit == invoice.total_ht
    assert entry.credit == invoice.total_ht
```

#### 5.3 Tests de Bout en Bout (E2E / API Tests)
Testent le flux complet via l'API.

```python
# sales/tests/test_api.py
@pytest.mark.django_db
def test_create_invoice_via_api(auth_client):
    """Test complet de création de facture via API"""
    payload = {
        "customer_id": customer.id,
        "lines": [{"product_id": product.id, "qty": 2, "price": 100}]
    }
    
    response = auth_client.post('/api/v1/sales/invoices/', payload)
    assert response.status_code == 201
    
    # Vérifier l'écriture comptable générée
    response = auth_client.get(f'/api/v1/finance/entries/?source=invoice_{response.data["id"]}')
    assert response.status_code == 200
    assert len(response.data['results']) == 1
```

#### 5.4 Tests de Performance (Pour modules critiques)
```python
# finance/tests/test_performance.py
def test_bulk_journal_entries_performance():
    """Créer 1000 écritures ne doit pas dépasser 5 secondes"""
    start_time = time.time()
    for i in range(1000):
        create_test_journal_entry()
    elapsed = time.time() - start_time
    assert elapsed < 5.0
```

### Commandes de Test

```bash
# Lancer tous les tests
pytest

# Lancer les tests d'un module spécifique
pytest finance/tests/ -v

# Lancer avec couverture de code
pytest --cov=. --cov-report=html --cov-report=term-missing

# Lancer uniquement les tests échoués précédemment
pytest --lf

# Lancer les tests en parallèle (gain de temps)
pytest -n auto
```

### Coverage Minimum Requis

| Module | Coverage Minimum |
|--------|------------------|
| Core | 95% |
| Finance | 95% |
| Sales | 90% |
| Purchases | 90% |
| Inventory | 90% |
| HR | 85% |
| Autres | 80% |

> 🚨 **Règle** : Si le coverage est inférieur au minimum, le pipeline CI/CD échoue et le merge est bloqué.

---

## 6. CHECKLIST DE VALIDATION PAR MODULE

Avant de considérer un module comme **TERMINÉ** et de passer au suivant, cocher TOUTES ces cases :

### ✅ Modèles de Données
- [ ] Tous les modèles du cahier des charges sont implémentés
- [ ] Champs `company` et `branch` ajoutés (si applicable)
- [ ] Indexes créés sur les champs de recherche fréquents
- [ ] Constraints uniques et vérifications intégrité
- [ ] Méthodes `__str__` définies pour tous les modèles
- [ ] Méthodes `save()` et `delete()` personnalisées si besoin
- [ ] Signals Django enregistrés et testés

### ✅ Logique Métier (Services)
- [ ] Fonctions principales implémentées dans `services/`
- [ ] Transactions atomiques (`@transaction.atomic`) là où nécessaire
- [ ] Gestion d'erreurs robuste (exceptions spécifiques)
- [ ] Logs appropriés (info, warning, error)
- [ ] Fonctions pures testables isolément

### ✅ API REST
- [ ] Serializers avec validation complète
- [ ] ViewSets avec actions CRUD complètes
- [ ] Permissions RBAC configurées et testées
- [ ] Pagination, filtering, ordering fonctionnels
- [ ] Documentation Swagger à jour et précise
- [ ] Codes HTTP appropriés (200, 201, 400, 401, 403, 404, 500)

### ✅ Tests
- [ ] Tests unitaires pour tous les modèles
- [ ] Tests unitaires pour tous les services
- [ ] Tests d'intégration avec modules dépendants
- [ ] Tests API pour tous les endpoints
- [ ] Coverage > seuil minimum requis
- [ ] Tous les tests passent en vert (`pytest` sans erreur)

### ✅ Intégration Finance (Si module métier)
- [ ] Les opérations génèrent des écritures comptables automatiques
- [ ] Tests d'intégration avec module `finance` validés
- [ ] Valorisation correcte (HT, TVA, TTC)
- [ ] Multi-devises géré si applicable

### ✅ Sécurité
- [ ] Authentification requise sur tous les endpoints
- [ ] Permissions vérifiées (RBAC)
- [ ] Injection SQL prévenue (ORM utilisé correctement)
- [ ] XSS prévenu (sanitization des inputs)
- [ ] Rate limiting configuré sur endpoints sensibles

### ✅ Documentation
- [ ] README du module créé avec exemples d'usage
- [ ] Docstrings sur toutes les fonctions publiques
- [ ] Commentaires pour logique complexe
- [ ] Fixtures de démo créées

### ✅ Performance
- [ ] Requêtes N+1 éliminées (utiliser `select_related`, `prefetch_related`)
- [ ] Indexes vérifiés avec `EXPLAIN ANALYZE` sur requêtes lourdes
- [ ] Tests de performance passés (si module critique)

### ✅ CI/CD
- [ ] Pipeline GitHub Actions passe en vert
- [ ] Build Docker fonctionnel
- [ ] Déploiement en environnement de test réussi

---

## 7. BONNES PRATIQUES DE CODE

### Conventions de Nommage
```python
# Modèles : PascalCase
class JournalEntry(models.Model):
    pass

# Fonctions/Méthodes : snake_case
def create_journal_entry():
    pass

# Constantes : UPPER_SNAKE_CASE
DEFAULT_CURRENCY = 'XAF'

# Variables privées : _prefix
_internal_cache = {}
```

### Principes SOLID
- **Single Responsibility** : Une classe/fonction = une responsabilité
- **Open/Closed** : Ouvert à l'extension, fermé à la modification
- **Liskov Substitution** : Les classes dérivées doivent être substituables
- **Interface Segregation** : Interfaces spécifiques plutôt que générales
- **Dependency Inversion** : Dépendre des abstractions, pas des implémentations

### Gestion des Exceptions
```python
# ❌ MAUVAIS
try:
    do_something()
except:
    pass

# ✅ BON
from rest_framework.exceptions import ValidationError

def validate_journal_entry(entry):
    if not entry.is_balanced():
        raise ValidationError("L'écriture doit être équilibrée (débit = crédit)")
```

### Optimisation des Requêtes
```python
# ❌ MAUVAIS (N+1 queries)
for invoice in Invoice.objects.all():
    print(invoice.customer.name)

# ✅ BON (2 queries max)
for invoice in Invoice.objects.select_related('customer').all():
    print(invoice.customer.name)

# ✅ BON POUR MANY-TO-MANY (prefetch_related)
for order in Order.objects.prefetch_related('lines__product').all():
    for line in order.lines.all():
        print(line.product.name)
```

### Transactions Atomiques
```python
from django.db import transaction

@transaction.atomic
def process_payment(invoice, amount):
    # Toutes les opérations réussissent ou aucune n'est appliquée
    invoice.status = 'PAID'
    invoice.save()
    
    JournalEntry.objects.create(...)
    BankTransaction.objects.create(...)
    
    # Si une exception est levée ici, tout est rollbacké
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)

def critical_operation():
    try:
        # ...
        logger.info("Opération réussie pour invoice_id=%s", invoice.id)
    except Exception as e:
        logger.error("Échec critique pour invoice_id=%s: %s", invoice.id, str(e), exc_info=True)
        raise
```

---

## 8. GESTION DES DÉPENDANCES ENTRE MODULES

### Règles d'Importation

```python
# ✅ AUTORISÉ : Core peut être importé par tous
from core.models import Company, Branch

# ✅ AUTORISÉ : Un module peut importer Core et Finance
from finance.services import create_journal_entry

# ❌ INTERDIT : Finance ne doit pas importer Sales/Purchases/etc.
# (Finance doit rester indépendant, utiliser des signaux ou événements)

# ✅ SOLUTION : Utiliser des signaux Django pour découpler
# sales/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save

@receiver(post_save, sender=Invoice)
def invoice_validated_handler(sender, instance, created, **kwargs):
    if instance.status == 'VALIDATED':
        # Appeler un service finance via une interface abstraite
        from finance.services import auto_generate_entry
        auto_generate_entry(instance)
```

### Pattern d'Événements (Event-Driven)

Pour éviter le couplage fort, utiliser un système d'événements :

```python
# core/events.py
from django.dispatch import Signal

# Signaux génériques
invoice_validated = Signal()
payment_received = Signal()
stock_movement_created = Signal()

# Utilisation dans sales/models.py
from core.events import invoice_validated

class Invoice(models.Model):
    def validate(self):
        # ... logique de validation
        self.status = 'VALIDATED'
        self.save()
        
        # Émettre l'événement
        invoice_validated.send(sender=self.__class__, instance=self)

# Écouteur dans finance/signals.py
from core.events import invoice_validated

@receiver(invoice_validated)
def handle_invoice_validated(sender, instance, **kwargs):
    # Générer l'écriture comptable
    create_journal_entry_from_invoice(instance)
```

---

## 9. COMMANDES UTILES

### Démarrage Environnement de Dev
```bash
# Construire et lancer les conteneurs
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

### Gestion Django
```bash
# Accéder au shell Django
docker-compose exec web python manage.py shell

# Créer une migration
docker-compose exec web python manage.py makemigrations <module_name>

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Créer un superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

### Tests
```bash
# Lancer tous les tests
docker-compose exec web pytest

# Lancer avec coverage
docker-compose exec web pytest --cov=. --cov-report=html

# Ouvrir le rapport de coverage
open htmlcov/index.html
```

### Base de Données
```bash
# Accéder à PostgreSQL
docker-compose exec db psql -U djosserp -d djosserp_dev

# Backup DB
docker-compose exec db pg_dump -U djosserp djosserp_dev > backup.sql

# Restore DB
docker-compose exec -T db psql -U djosserp -d djosserp_dev < backup.sql
```

### Qualité de Code
```bash
# Formater le code (Black)
black .

# Vérifier le style (Flake8)
flake8 .

# Vérifier les types (MyPy)
mypy .

# Exécuter tous les checks pre-commit
pre-commit run --all-files
```

---

## 10. DÉPANNAGE & FAQ

### Problème : Migrations en conflit
```bash
# Solution : Fusionner les migrations
python manage.py makemigrations --merge
```

### Problème : Tests lents
```bash
# Utiliser pytest-xdist pour paralléliser
pytest -n auto

# Identifier les tests lents
pytest --durations=10
```

### Problème : Requêtes N+1
```bash
# Activer Django Debug Toolbar
# Ou utiliser django-silk pour profiler les requêtes
```

### Problème : Coverage faible
```bash
# Identifier les lignes non couvertes
pytest --cov-report=term-missing

# Cibler les fonctions critiques en priorité
```

### Problème : Import circulaire
```python
# ❌ ERREUR
# module_a.py
from module_b import something

# module_b.py
from module_a import something_else

# ✅ SOLUTION
# Déplacer l'import à l'intérieur de la fonction qui en a besoin
# OU utiliser des imports différés
# OU refactoriser pour extraire la logique commune dans un troisième module
```

### Problème : Écritures comptables déséquilibrées
```python
# Toujours valider avant de sauver
def save(self, *args, **kwargs):
    if not self.is_balanced():
        raise ValidationError("Écriture déséquilibrée")
    super().save(*args, **kwargs)
```

---

## 🎯 CHECKLIST FINALE AVANT PREMIÈRE VERSION (MVP)

Avant de livrer la première version utilisable de Djoss-ERP :

- [ ] Module Core fonctionnel (Auth, RBAC, Multi-tenancy)
- [ ] Module Finance fonctionnel (Plan comptable, Écritures, États de base)
- [ ] Module Sales fonctionnel (Devis → Facture → Paiement)
- [ ] Module Purchases fonctionnel (Commande → Facture fournisseur → Paiement)
- [ ] Module Inventory fonctionnel (Entrées/Sorties → Valorisation)
- [ ] Intégration Finance ↔ Tous modules métiers validée
- [ ] Coverage global > 85%
- [ ] Documentation API complète
- [ ] Tests E2E pour les workflows critiques
- [ ] Déploiement automatisé fonctionnel
- [ ] Manuel utilisateur de base rédigé

---

## 📞 SUPPORT & RESSOURCES

- **Documentation Django** : https://docs.djangoproject.com/
- **Django REST Framework** : https://www.django-rest-framework.org/
- **pytest** : https://docs.pytest.org/
- **Cahier des Charges Djoss-ERP** : `CAHIER DES CHARGES — DJOSS-ERP.md`
- **Slack/Communication** : Canal #dev-djosserp

---

**Dernière mise à jour** : $(date +%Y-%m-%d)  
**Maintenu par** : Équipe de Développement Djoss-ERP

> 💡 **RAPPEL FINAL** : La qualité prime sur la vitesse. Mieux vaut un module terminé en 2 semaines avec 95% de coverage et zéro bug, qu'un module bâclé en 3 jours qui devra être entièrement réécrit.

**BON COURAGE ET BON CODAGE ! 🚀**
