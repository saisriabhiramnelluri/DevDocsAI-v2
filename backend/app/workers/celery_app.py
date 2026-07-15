"""
DevDocsAI — Celery App Configuration
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "devdocsai",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.analysis_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.analysis_tasks.analyze_repository": {"queue": "analysis"},
    },
    task_soft_time_limit=600,   # 10 min soft limit
    task_time_limit=720,         # 12 min hard limit
)
