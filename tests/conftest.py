"""
Pytest fixtures for Resume Analyzer API tests.
"""
import os

import pytest
from fastapi.testclient import TestClient

# Use test DB when running tests (optional; can use SQLite for unit tests later)
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/resume_analyzer_test")


@pytest.fixture
def client():
    """FastAPI test client."""
    from app.main import app
    return TestClient(app)
