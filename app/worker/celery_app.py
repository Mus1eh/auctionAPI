from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "auction",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

celery_app.conf.beat_schedule = {
    "close-expired-auctions": {
        "task": "app.tasks.close_expired_auctions",
        "schedule": 10.0,
    },
    "process-email-outbox": {
        "task": "app.tasks.process_email_outbox",
        "schedule": 10.0,
    },
}

celery_app.conf.timezone = "UTC"
celery_app.conf.result_expires = settings.celery_result_expires
