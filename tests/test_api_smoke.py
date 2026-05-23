from fastapi.testclient import TestClient

from backend.main import app
from backend.settings import settings


client = TestClient(app)


def _restore_pappers_settings(mock_mode: bool, api_key: str) -> None:
    settings.pappers_mock_mode = mock_mode
    settings.pappers_api_key = api_key


def test_root_ok():
    response = client.get("/")
    assert response.status_code == 200


def test_dossiers_crud_create_update_delete():
    created_id = None
    try:
        create_response = client.post(
            "/dossiers/",
            json={
                "nom_entreprise": "Test CRUD ERP Rosan",
                "cp": "75001",
                "ville": "Paris",
                "type_dossier": "BIC",
            },
        )
        assert create_response.status_code == 200
        created = create_response.json()
        created_id = created["id"]
        assert created["num_dossier"] == f"DOS-{created_id:06d}"
        assert created["nom_entreprise"] == "Test CRUD ERP Rosan"

        get_response = client.get(f"/dossiers/{created_id}")
        assert get_response.status_code == 200
        assert get_response.json()["cp"] == "75001"

        update_response = client.put(
            f"/dossiers/{created_id}",
            json={"nom_entreprise": "Test CRUD ERP Rosan Modifié", "ville": "Lyon"},
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["nom_entreprise"] == "Test CRUD ERP Rosan Modifié"
        assert updated["ville"] == "Lyon"
        assert updated["cp"] == "75001"

        delete_response = client.delete(f"/dossiers/{created_id}")
        assert delete_response.status_code == 200

        missing_response = client.get(f"/dossiers/{created_id}")
        assert missing_response.status_code == 404
        created_id = None
    finally:
        if created_id is not None:
            client.delete(f"/dossiers/{created_id}")


def test_pappers_invalid_siret_returns_400():
    previous_mock = settings.pappers_mock_mode
    previous_key = settings.pappers_api_key
    try:
        settings.pappers_mock_mode = False
        settings.pappers_api_key = ""
        response = client.get("/dossiers/from-pappers/123")
        assert response.status_code == 400
    finally:
        _restore_pappers_settings(previous_mock, previous_key)


def test_pappers_missing_key_returns_503():
    previous_mock = settings.pappers_mock_mode
    previous_key = settings.pappers_api_key
    try:
        settings.pappers_mock_mode = False
        settings.pappers_api_key = ""
        response = client.get("/dossiers/from-pappers/41816609600069")
        assert response.status_code == 503
    finally:
        _restore_pappers_settings(previous_mock, previous_key)


def test_pappers_mock_mode_returns_payload():
    previous_mock = settings.pappers_mock_mode
    previous_key = settings.pappers_api_key
    try:
        settings.pappers_mock_mode = True
        settings.pappers_api_key = ""
        response = client.get("/dossiers/from-pappers/41816609600069")
        assert response.status_code == 200
        data = response.json()
        assert data["siret"] == "41816609600069"
        assert data["siren"] == "418166096"
        assert "nom_entreprise" in data
    finally:
        _restore_pappers_settings(previous_mock, previous_key)


def test_accounting_bootstrap_and_balanced_entry():
    created_id = None
    try:
        create_response = client.post(
            "/dossiers/",
            json={
                "nom_entreprise": "Test Compta ERP Rosan",
                "type_dossier": "BIC",
            },
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        features_response = client.get("/accounting/features")
        assert features_response.status_code == 200
        assert features_response.json()["inventory"]["installed"] is True

        bootstrap_response = client.post(f"/accounting/dossiers/{created_id}/bootstrap")
        assert bootstrap_response.status_code == 200
        status = bootstrap_response.json()
        assert status["ready"] is True
        assert status["journals"] >= 6
        assert status["accounts"] >= 10

        fiscal_years = client.get(f"/accounting/dossiers/{created_id}/fiscal-years").json()
        journals = client.get(f"/accounting/dossiers/{created_id}/journals").json()
        fiscal_year_id = fiscal_years[0]["id"]
        journal_id = next(j["id"] for j in journals if j["code"] == "OD")

        unbalanced_response = client.post(
            f"/accounting/dossiers/{created_id}/entries",
            json={
                "fiscal_year_id": fiscal_year_id,
                "journal_id": journal_id,
                "entry_date": "2026-01-15",
                "label": "Ecriture non equilibree",
                "lines": [
                    {"account_number": "512000", "debit": "100.00", "credit": "0.00"},
                    {"account_number": "706000", "debit": "0.00", "credit": "90.00"},
                ],
            },
        )
        assert unbalanced_response.status_code == 400

        entry_response = client.post(
            f"/accounting/dossiers/{created_id}/entries",
            json={
                "fiscal_year_id": fiscal_year_id,
                "journal_id": journal_id,
                "entry_date": "2026-01-15",
                "piece_number": "TEST-001",
                "label": "Ecriture equilibree",
                "lines": [
                    {"account_number": "512000", "debit": "120.00", "credit": "0.00"},
                    {"account_number": "706000", "debit": "0.00", "credit": "100.00"},
                    {"account_number": "445710", "debit": "0.00", "credit": "20.00"},
                ],
            },
        )
        assert entry_response.status_code == 200
        entry = entry_response.json()
        assert entry["label"] == "Ecriture equilibree"
        assert len(entry["lines"]) == 3

        balance_response = client.get(f"/accounting/dossiers/{created_id}/trial-balance")
        assert balance_response.status_code == 200
        balance = balance_response.json()
        assert any(row["account_number"] == "512000" for row in balance)

        ledger_response = client.get(f"/accounting/dossiers/{created_id}/ledger")
        assert ledger_response.status_code == 200
        ledger = ledger_response.json()
        assert len(ledger) == 3
        assert ledger[0]["journal_code"] == "OD"

    finally:
        if created_id is not None:
            client.delete(f"/dossiers/{created_id}")
