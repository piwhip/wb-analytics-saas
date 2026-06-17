from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "wb_analytics",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)

celery_app.conf.beat_schedule = {
    "sync-all-users-hourly": {
        "task": "app.workers.tasks.sync_all_users_task",
        "schedule": crontab(minute=0),
        "kwargs": {"days_back": 2},
    },
    "low-stock-alerts-daily": {
        "task": "app.workers.tasks.low_stock_alerts_task",
        "schedule": crontab(hour=9, minute=0),
        "kwargs": {"threshold": 5},
    },
    "daily-summary": {
        "task": "app.workers.tasks.daily_summary_task",
        "schedule": crontab(hour=18, minute=0),
    },
}
