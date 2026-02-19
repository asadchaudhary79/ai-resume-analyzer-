"""
Application configuration using pydantic-settings.
Loads from environment variables and .env file.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "AI-Powered Resume Analyzer API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (PostgreSQL)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/resume_analyzer"

    # Redis (Phase 5 — Celery broker)
    redis_url: str = "redis://localhost:6379/0"

    # File uploads
    upload_dir: Path = Path("uploads")
    max_upload_size_mb: int = 5

    # CORS — allow all origins for public API
    cors_origins: List[str] = ["*"]

    # OpenAI (Phase 3)
    openai_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
