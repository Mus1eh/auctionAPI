from celery import Celery

celery_app = Celery(
    "auction",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.tasks"],
)

celery_app.conf.beat_schedule = {
    "close-expired-auctions": {
        "tasks": "app.tasks.close_expired_auctions",
        "schedule": 10,
    }
}

celery_app.conf.timezone = "UTC"
