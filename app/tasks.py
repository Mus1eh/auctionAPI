from datetime import UTC, datetime

from app.celery_app import celery_app
from app.database import sessionLocal
from app.email_service import send_auction_email
from app.repositories.bids import BidRepository
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.product import ProductRepository
from app.services.auctions.close import close_auction


@celery_app.task(name="app.tasks.close_expired_auctions")
def close_expired_auctions():
    db = sessionLocal()

    try:
        now = datetime.now(UTC)

        expired_auctions = ProductRepository(db).get_expired_active_for_update(now)
        outbox_repo = EmailOutboxRepository(db)
        bid_repo = BidRepository(db)

        for product in expired_auctions:
            close_auction(db, product, outbox_repo, bid_repo)

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
        outbox_repo = EmailOutboxRepository(db)
        try:
            email = outbox_repo.get_next_pending_for_update()
            if not email:
                break

            try:
                send_auction_email(
                    to_email=email.to_email,
                    subject=email.subject,
                    body=email.body,
                )

            except Exception as exc:  # NOQA
                outbox_repo.mark_failed(email)
                db.commit()
                failed_count += 1
                print(f"Failed to send email #{email.id}: {exc}")

            else:
                outbox_repo.mark_sent(email)
                db.commit()
                sent_count += 1

        finally:
            db.close()

    return {
        "sent": sent_count,
        "failed": failed_count,
    }
