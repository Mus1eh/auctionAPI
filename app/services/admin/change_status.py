from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ProductNotFoundError,
    SameStatusError,
)
from app.enums import ProductStatus
from app.repositories.bids import BidRepository
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.product import ProductRepository
from app.services.auctions.close import close_auction


def change_product_status(
    db: Session,
    product_repo: ProductRepository,
    product_id: int,
    status_value: ProductStatus,
    outbox_repo: EmailOutboxRepository,
    bid_repo: BidRepository,
):
    try:
        product = product_repo.get_by_id_for_update(product_id)

        if product is None:
            raise ProductNotFoundError()

        if product.status == status_value:
            raise SameStatusError()

        if status_value == ProductStatus.CLOSED:
            if product.status != ProductStatus.ACTIVE:
                raise ConflictError("Only active auctions can be closed.")
            bid_repo = BidRepository(db)
            close_auction(product, outbox_repo, bid_repo)

        elif status_value == ProductStatus.ACTIVE:
            if product.status != ProductStatus.DRAFT:
                raise ConflictError("Only draft products can be activated.")

            now = datetime.now(UTC)

            product_repo.update(
                product,
                {
                    "status": ProductStatus.ACTIVE,
                    "auction_started_at": now,
                    "auction_ends_at": now + timedelta(hours=1),
                },
            )

        else:
            raise BadRequestError(
                "This endpoint supports activating or closing auctions only."
            )

        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise
