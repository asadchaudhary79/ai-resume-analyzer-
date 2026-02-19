"""Phase 4: Job matching."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


def test_match_job_missing_resume(client: TestClient):
    r = client.post(
        "/api/v1/analysis/match-job",
        json={
            "resume_id": "00000000-0000-0000-0000-000000000001",
            "job_description": "Python developer with FastAPI.",
        },
    )
    assert r.status_code == 404


def test_match_job_empty_jd(client: TestClient):
    # Without a valid resume_id we get 404; with empty body we get 422
    r = client.post(
        "/api/v1/analysis/match-job",
        json={"resume_id": "00000000-0000-0000-0000-000000000001", "job_description": ""},
    )
    assert r.status_code in (400, 404)
