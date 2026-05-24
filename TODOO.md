# TODOO - Ce qui reste à faire pour le projet global Djoss ERP

## 🎯 OBJECTIF GLOBAL
Créer un ERP complet de type Sage/Odoo/Dolibarr avec tous les modules métier intégrés.

---

## 📋 MODULE FINANCE - À FINALISER

### Haute Priorité
- [ ] **Liasses fiscales** : Formulaire 2035, 2050, 2051, 2055, 2056, 2057, 2058
- [ ] **Budgets** : Création, suivi, alertes budgétaires
- [ ] **Tableaux de flux de trésorerie** : Méthode directe et indirecte
- [ ] **États financiers complets** : Bilan, Compte de résultat, Annexes
- [ ] **Clôture d'exercice** : Procédure automatique de clôture
- [ ] **Réouverture d'exercice** : Report à nouveau automatique

### Moyenne Priorité
- [ ] **Lettrage automatique avancé** : Par référence, par montant, par date
- [ ] **Rapprochement bancaire intelligent** : Matching algorithmique
- [ ] **Gestion des échéances** : Relances clients automatiques
- [ ] **Export FEC conforme** : Validation ANFC complète
- [ ] **Piste d'audit Fichier** : Export complet avec horodatage

### Basse Priorité
- [ ] **Multi-devises** : Gestion des écarts de conversion
- [ ] **Consolidation** : Regroupement de plusieurs dossiers
- [ ] **Analytique avancée** : Clés de répartition, sous-sections

---

## 📦 MODULES MÉTIER - À DÉVELOPPER

### 1. Module VENTES (Sales) 🔴 PRIORITAIRE
**Dépendance** : Finance ✔
**Fichiers à créer** :
```
/workspace/sales/
├── models/
│   ├── quotation.py          # Devis
│   ├── sale_order.py         # Bons de commande
│   ├── invoice.py            # Factures clients
│   └── delivery.py           # Bons de livraison
├── services/
│   ├── quotation_service.py
│   ├── invoice_service.py
│   └── sale_to_accounting.py # Génération écritures comptables
├── api/
│   └── routes_sales.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Devis → Bon de commande → Facture
- [ ] Relances automatiques
- [ ] Statistiques ventes
- [ ] Intégration comptable automatique (70x, 411x, 4457x)

### 2. Module ACHATS (Purchases) 🔴 PRIORITAIRE
**Dépendance** : Finance ✔
**Fichiers à créer** :
```
/workspace/purchases/
├── models/
│   ├── rfq.py                # Demandes de prix
│   ├── purchase_order.py     # Commandes fournisseurs
│   ├── vendor_bill.py        # Factures fournisseurs
│   └── receipt.py            # Réceptions
├── services/
│   ├── purchase_service.py
│   ├── bill_service.py
│   └── purchase_to_accounting.py # Génération écritures
├── api/
│   └── routes_purchases.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Demande de prix → Commande → Réception → Facture
- [ ] Contrôle facture/commande/réception
- [ ] Intégration comptable automatique (60x, 401x, 4456x)

### 3. Module STOCK (Inventory) 🟡 MOYENNE PRIORITÉ
**Dépendance** : Ventes + Achats
**Fichiers à créer** :
```
/workspace/inventory/
├── models/
│   ├── product.py            # Articles
│   ├── warehouse.py          # Entrepôts
│   ├── stock_move.py         # Mouvements de stock
│   └── stock_valuation.py    # Valorisation
├── services/
│   ├── product_service.py
│   ├── move_service.py
│   └── valuation_service.py
├── api/
│   └── routes_inventory.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Gestion multi-entrepôts
- [ ] Suivi des mouvements (entrées/sorties/transferts)
- [ ] Valorisation (PMP, FIFO, LIFO)
- [ ] Inventaires périodiques
- [ ] Alertes stock minimum

### 4. Module RESSOURCES HUMAINES (HR) 🟡 MOYENNE PRIORITÉ
**Dépendance** : Finance (pour la paie)
**Fichiers à créer** :
```
/workspace/hr/
├── models/
│   ├── employee.py           # Employés
│   ├── contract.py           # Contrats
│   ├── timesheet.py          # Feuilles de temps
│   ├── leave.py              # Congés
│   └── payroll.py            # Paie
├── services/
│   ├── employee_service.py
│   ├── payroll_service.py
│   └── hr_to_accounting.py   # Écritures de paie
├── api/
│   └── routes_hr.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Gestion du personnel
- [ ] Contrats de travail
- [ ] Suivi des congés/absences
- [ ] Bulletins de paie
- [ ] Intégration comptable (64x, 421x, 431x, 444x)

### 5. Module CRM 🟢 BASSE PRIORITÉ
**Dépendance** : Aucune
**Fichiers à créer** :
```
/workspace/crm/
├── models/
│   ├── lead.py               # Pistes
│   ├── opportunity.py        # Opportunités
│   ├── partner.py            # Partenaires
│   └── activity.py           # Activités
├── services/
│   ├── crm_service.py
│   └── pipeline_service.py
├── api/
│   └── routes_crm.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Pipeline de ventes
- [ ] Suivi des opportunités
- [ ] Historique des interactions
- [ ] Conversion Lead → Client

### 6. Module PROJETS 🟢 BASSE PRIORITÉ
**Dépendance** : CRM + Ventes
**Fichiers à créer** :
```
/workspace/projects/
├── models/
│   ├── project.py            # Projets
│   ├── task.py               # Tâches
│   └── milestone.py          # Jalons
├── services/
│   ├── project_service.py
│   └── task_service.py
├── api/
│   └── routes_projects.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Gestion de projets
- [ ] Planification des tâches
- [ ] Suivi du temps passé
- [ ] Facturation au temps passé

### 7. Module PRODUCTIVITÉ 🟢 BASSE PRIORITÉ
**Dépendance** : Tous les modules
**Fichiers à créer** :
```
/workspace/productivity/
├── models/
│   ├── document.py           # GED
│   ├── calendar.py           # Agenda
│   └── notification.py       # Notifications
├── services/
│   ├── document_service.py
│   └── notification_service.py
├── api/
│   └── routes_productivity.py
├── tests/
└── fixtures/
```

**Fonctionnalités** :
- [ ] Gestion électronique des documents
- [ ] Agenda partagé
- [ ] Système de notifications
- [ ] Tableaux de bord personnalisés

---

## 🔧 INFRASTRUCTURE TECHNIQUE - À AMÉLIORER

### Backend API
- [ ] **API REST complète** : Endpoints pour tous les modèles
- [ ] **Authentification JWT** : Login/Logout, refresh tokens
- [ ] **Permissions RBAC** : Rôles et permissions granulaires
- [ ] **Documentation Swagger/OpenAPI** : Auto-générée
- [ ] **Rate limiting** : Protection contre les abus

### Base de données
- [ ] **Migrations Alembic** : Scripts de migration versionnés
- [ ] **Backup automatique** : Sauvegarde quotidienne
- [ ] **Indexation avancée** : Optimisation des requêtes
- [ ] **Audit des données** : Qui a fait quoi et quand

### Tests & Qualité
- [ ] **Tests d'intégration** : Scénarios complets
- [ ] **Tests E2E** : Avec Playwright ou Selenium
- [ ] **CI/CD** : GitHub Actions pour build/test/deploy
- [ ] **Couverture > 90%** : Sur les modules critiques
- [ ] **Linting** : Black, Flake8, MyPy

### Performance
- [ ] **Cache Redis** : Pour les données fréquemment consultées
- [ ] **File d'attente Celery** : Tâches asynchrones
- [ ] **Optimisation SQL** : Requêtes N+1 à éliminer
- [ ] **Pagination** : Sur toutes les listes

---

## 🖥️ FRONTEND - À DÉVELOPPER

### Modules PySide6 restants
- [ ] **Module Ventes** : Interface complète (devis, commandes, factures)
- [ ] **Module Achats** : Interface complète (commandes, factures)
- [ ] **Module Stock** : Interface (produits, mouvements, inventaires)
- [ ] **Module RH** : Interface (employés, congés, paie)
- [ ] **Module CRM** : Interface (pipeline, opportunités)
- [ ] **Module Projets** : Interface (tâches, planning)

### Améliorations UI/UX
- [ ] **Thème sombre/clair** : Bascule utilisateur
- [ ] **Responsive design** : Adaptation différentes résolutions
- [ ] **Accessibilité** : Normes WCAG
- [ ] **Internationalisation** : Traduction FR → EN (prévu après stabilisation)

---

## 📊 TABLEAU DE BORD & REPORTING

### Tableaux de bord à créer
- [ ] **Dashboard Direction** : KPI globaux (CA, marge, trésorerie)
- [ ] **Dashboard Commercial** : Ventes par période, par commercial
- [ ] **Dashboard Achats** : Dépenses, fournisseurs principaux
- [ ] **Dashboard RH** : Effectif, masse salariale, absentéisme
- [ ] **Dashboard Projet** : Avancement, budget vs réel

### États légaux
- [ ] **Bilan** : Actif/Passif
- [ ] **Compte de résultat** : Produits/Charges
- [ ] **Tableau des flux de trésorerie**
- [ ] **Annexes comptables**
- [ ] **Liasse fiscale** : Formulaire 2035 et suivants

---

## 🚀 DÉPLOIEMENT & PRODUCTION

### Docker & Orchestration
- [ ] **Dockerfile optimisé** : Multi-stage build
- [ ] **docker-compose.yml** : Services PostgreSQL, Redis, etc.
- [ ] **Kubernetes** : Déploiement scalable (optionnel)

### Monitoring & Logs
- [ ] **Logs centralisés** : ELK Stack ou équivalent
- [ ] **Monitoring** : Prometheus + Grafana
- [ ] **Alerting** : En cas d'erreur ou de performance dégradée

### Sécurité
- [ ] **HTTPS obligatoire** : Certificats SSL/TLS
- [ ] **Protection CSRF/XSS** : Headers de sécurité
- [ ] **Validation des entrées** : Sanitization systématique
- [ ] **Chiffrement des données sensibles** : Mots de passe, données bancaires

---

## 📅 ROADMAP PROPOSÉE

### Phase 1 (Immédiat - 2 semaines)
- Finaliser module Finance (liasses, budgets, clôtures)
- Tests approfondis sur module Finance
- Documentation utilisateur

### Phase 2 (1 mois)
- Module Ventes complet
- Module Achats complet
- Intégration comptable automatique

### Phase 3 (2 mois)
- Module Stock
- Module RH (paie)
- Tableaux de bord métiers

### Phase 4 (3 mois)
- Module CRM
- Module Projets
- Module Productivité

### Phase 5 (4-6 mois)
- Internationalisation (EN)
- Optimisations performance
- Préparation production

---

## 📝 NOTES IMPORTANTES

1. **Priorité absolue** : La comptabilité doit être parfaite avant tout module métier
2. **Tests obligatoires** : Aucun module ne sera validé sans tests TDD
3. **Documentation** : Chaque fonctionnalité doit avoir sa doc utilisateur
4. **PostgreSQL uniquement** : Plus de fallback SQLite
5. **Multi-tenancy** : Architecture 1 dossier = 1 base PostgreSQL maintenue

---

*Dernière mise à jour : 24 Mai 2025*
