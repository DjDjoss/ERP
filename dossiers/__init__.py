# -*- coding: utf-8 -*-
"""
Module Dossiers - Gestion des dossiers clients (multi-tenancy)

Architecture Django-like :
- models/ : Modèles de données SQLAlchemy
- services/ : Logique métier (création dossier, initialisation, etc.)
- api/ : Routes FastAPI et schémas Pydantic
- tests/ : Tests unitaires et d'intégration (TDD)
- factories/ : Factory Boy pour données de test
- fixtures/ : Données de démonstration
"""

__version__ = "1.0.0"
