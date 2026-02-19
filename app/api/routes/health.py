"""
Health check and system status endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns server and database status. Use this to verify the API is running and DB is reachable.",
)
def health_check(db: Session = Depends(get_db)):
    """Health check — server status and DB connectivity."""
    settings = get_settings()
    status = "ok"
    db_status = "unknown"

    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
        status = "degraded"

    return {
        "status": status,
        "service": settings.app_name,
        "database": db_status,
        "version": "1.0.0",
    }
