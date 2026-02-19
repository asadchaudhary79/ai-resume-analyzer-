"""Phase 3: Analysis endpoints."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_get_analysis_not_found(client: TestClient):
    r = client.get("/api/v1/analysis/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 404


def test_analysis_history(client: TestClient):
    r = client.get("/api/v1/analysis/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_match_history(client: TestClient):
    r = client.get("/api/v1/analysis/match-history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
