from celery import Celery

celery_app = Celery(
    "auction",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.tasks"],
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
