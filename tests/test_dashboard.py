"""Phase 6: Dashboard."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_dashboard_stats(client: TestClient):
    r = client.get("/api/v1/dashboard/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_resumes" in data
    assert "average_score" in data
    assert "best_score" in data
    assert "total_job_matches" in data


def test_improvement_trend(client: TestClient):
    r = client.get("/api/v1/dashboard/improvement-trend")
    assert r.status_code == 200
    data = r.json()
    assert "improvement_over_time" in data
    assert isinstance(data["improvement_over_time"], list)
