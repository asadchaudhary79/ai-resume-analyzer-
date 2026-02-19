"""
AI-Powered Resume Analyzer API — FastAPI application.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.database import init_db
from app.api.routes import health, resume, analysis, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure uploads dir exists and DB tables are created."""
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    yield
    # Shutdown: nothing to do for now


def create_app() -> FastAPI:
    settings = get_settings()

    limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])
    app = FastAPI(
        title=settings.app_name,
        description="Upload PDF/DOCX resumes, get AI-powered scores and suggestions, and match against job descriptions.",
        version="1.0.0",
        docs_url=f"{settings.api_v1_prefix}/docs",
        redoc_url=f"{settings.api_v1_prefix}/redoc",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS — allow all origins for public access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": type(exc).__name__,
            },
        )

    # API v1 routes
    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(resume.router, prefix=settings.api_v1_prefix)
    app.include_router(analysis.router, prefix=settings.api_v1_prefix)
    app.include_router(dashboard.router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    def root():
        return {
            "name": settings.app_name,
            "version": "1.0.0",
            "docs": f"{settings.api_v1_prefix}/docs",
            "health": f"{settings.api_v1_prefix}/health",
        }

    return app


app = create_app()
