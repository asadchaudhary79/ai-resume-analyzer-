"""Phase 2: Resume upload and CRUD."""
import io
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes():
    # Minimal valid PDF content
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"


def test_upload_resume_invalid_type(client: TestClient):
    r = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("resume.txt", io.BytesIO(b"not a pdf"), "text/plain")},
    )
    assert r.status_code == 400


def test_list_resumes(client: TestClient):
    r = client.get("/api/v1/resumes/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_resume_not_found(client: TestClient):
    r = client.get("/api/v1/resumes/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 404
