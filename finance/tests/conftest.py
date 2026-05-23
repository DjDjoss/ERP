# -*- coding: utf-8 -*-
"""
Configuration de pytest pour le module Finance
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.connection_manager import Base


@pytest.fixture(scope="session")
def test_engine():
    """Crée un moteur de base de données de test en mémoire"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(test_engine):
    """Crée une session de test avec rollback automatique"""
    TestingSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_dossier_id():
    """ID de dossier fictif pour les tests"""
    return 1
