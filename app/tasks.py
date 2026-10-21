from datetime import UTC, datetime

from app import models
from app.celery_app import celery_app
from app.database import sessionLocal
from app.enums import ProductStatus


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
        # using skip_locked to avoid waiting for locks held by other transactions useful in multi-worker environments
        for product in expired_auctions:
            product.status = ProductStatus.CLOSED

        closed_count = len(expired_auctions)

        db.commit()

        return {
            "Closed auctions": closed_count,
        }
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
