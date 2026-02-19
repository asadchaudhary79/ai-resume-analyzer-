"""
Celery application — Redis broker, used for background analysis and cleanup.
"""
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "resume_analyzer",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.celery_tasks"],
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        "cleanup-old-files": {
            "task": "app.tasks.celery_tasks.cleanup_old_files",
            "schedule": 86400.0,  # every 24 hours
        },
    },
)
