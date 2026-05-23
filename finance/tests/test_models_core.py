# -*- coding: utf-8 -*-
"""
Tests unitaires pour le modèle FiscalYear
"""

import pytest
from datetime import date, timedelta
from finance.models.core import FiscalYear


class TestFiscalYear:
    """Tests pour le modèle FiscalYear"""

    def test_create_fiscal_year(self, db_session, sample_dossier_id):
        """Test de création d'un exercice"""
        fiscal_year = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Exercice 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="draft",
        )
        
        db_session.add(fiscal_year)
        db_session.commit()
        db_session.refresh(fiscal_year)
        
        assert fiscal_year.id is not None
        assert fiscal_year.label == "Exercice 2025"
        assert fiscal_year.status == "draft"

    def test_is_open(self, db_session, sample_dossier_id):
        """Test de la méthode is_open"""
        # Exercice ouvert
        fy_open = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Ouvert",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="open",
        )
        db_session.add(fy_open)
        db_session.commit()
        
        assert fy_open.is_open() is True
        
        # Exercice fermé
        fy_closed = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Fermé",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            status="closed",
        )
        db_session.add(fy_closed)
        db_session.commit()
        
        assert fy_closed.is_open() is False

    def test_contains_date(self, db_session, sample_dossier_id):
        """Test de la méthode contains_date"""
        fiscal_year = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Exercice 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        
        # Date dans l'exercice
        assert fiscal_year.contains_date(date(2025, 6, 15)) is True
        
        # Date avant l'exercice
        assert fiscal_year.contains_date(date(2024, 12, 31)) is False
        
        # Date après l'exercice
        assert fiscal_year.contains_date(date(2026, 1, 1)) is False
        
        # Dates limites
        assert fiscal_year.contains_date(date(2025, 1, 1)) is True
        assert fiscal_year.contains_date(date(2025, 12, 31)) is True

    def test_unique_constraint_label(self, db_session, sample_dossier_id):
        """Test de l'unicité du label par dossier"""
        fy1 = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Exercice 2025",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
        db_session.add(fy1)
        db_session.commit()
        
        # Tentative de créer un deuxième exercice avec le même label
        fy2 = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Exercice 2025",
            start_date=date(2025, 4, 1),
            end_date=date(2026, 3, 31),
        )
        db_session.add(fy2)
        
        with pytest.raises(Exception):
            db_session.commit()

    def test_dates_constraint(self, db_session, sample_dossier_id):
        """Test que end_date >= start_date"""
        fiscal_year = FiscalYear(
            dossier_id=sample_dossier_id,
            label="Invalide",
            start_date=date(2025, 12, 31),
            end_date=date(2025, 1, 1),  # Incohérent
        )
        
        db_session.add(fiscal_year)
        
        with pytest.raises(Exception):
            db_session.commit()
