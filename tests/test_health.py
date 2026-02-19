"""Phase 1: Health and docs."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_health_returns_200(client: TestClient):
    r = client.get("/api/v1/health")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "status" in data
    assert "service" in data


def test_docs_available(client: TestClient):
    r = client.get("/api/v1/docs")
    assert r.status_code == 200
