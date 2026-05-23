# -*- coding: utf-8 -*-
"""
Module Finance - Cœur comptable de DJOSS-ERP

Architecture Django-like :
- models/ : Modèles de données SQLAlchemy
- services/ : Logique métier (création écritures, états financiers, etc.)
- api/ : Routes FastAPI et schémas Pydantic
- tests/ : Tests unitaires et d'intégration (TDD)
- factories/ : Factory Boy pour données de test
"""

__version__ = "1.0.0"
