from celery import Celery

celery_app = Celery(
    "auction",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["app.tasks"],
)

celery_app.conf.beat_schedule = {
    "closed-expired-auctions": {
        "task": "app.tasks.close_expired_auctions",
        "schedule": 10.0,  # RUNS EVERY 10 SECONDS
    }
}

celery_app.conf.timezone = "UTC"
