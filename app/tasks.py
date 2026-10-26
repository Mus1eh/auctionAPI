from datetime import UTC, datetime

from app import models
from app.celery_app import celery_app
from app.database import sessionLocal
from app.email_service import send_auction_email
from app.enums import ProductStatus
from app.services.auction_service import close_auction


@celery_app.task(name="app.tasks.close_expired_auctions")
def close_expired_auctions():
    db = sessionLocal()

    try:
        now = datetime.now(UTC)

        expired_auctions = (
            db.query(models.Product)
            .filter(
                models.Product.status == ProductStatus.ACTIVE,
                models.Product.auction_ends_at <= now,
            )
            .with_for_update(skip_locked=True)
            .all()
        )

        for product in expired_auctions:
            close_auction(db, product)

        closed_count = len(expired_auctions)

        db.commit()

        return {
            "Closed Auctions": closed_count,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.send_auction_notification",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_auction_notification(self, to_email: str, subject: str, body: str):
    send_auction_email(to_email=to_email, subject=subject, body=body)

    return {
        "status": "sent",
        "recipient": to_email,
    }


@celery_app.task(name="app.tasks.process_email_outbox")
def process_email_outbox():

    sent_count = 0
    failed_count = 0
    for _ in range(20):
        db = sessionLocal()
        try:
            email = (
                db.query(models.EmailOutbox)
                .filter(models.EmailOutbox.status == "pending")
                .order_by(models.EmailOutbox.id)
                .with_for_update(skip_locked=True)
                .first()
            )

            if not email:
                break

            email_id = email.id

            try:
                send_auction_email(
                    to_email=email.to_email,
                    subject=email.subject,
                    body=email.body,
                )

                email.status = "sent"
                email.sent_at = datetime.now(UTC)

                db.commit()
                sent_count += 1

            except Exception as exc:  # NOQA
                db.rollback()
                failed_count += 1

                print(f"Failed to send email #{email_id}: {exc}")

            return {
                "sent": sent_count,
                "failed": failed_count,
            }

        finally:
            db.close()
