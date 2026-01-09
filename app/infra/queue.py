"""Celery configuration and setup."""

from celery import Celery

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "expense_tracker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.modules.reports.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute
    task_routes={
        "app.modules.reports.tasks.*": {"queue": "reports"},
    },
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

logger.info("Celery app configured", extra={"broker": settings.CELERY_BROKER_URL})
