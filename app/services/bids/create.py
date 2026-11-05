from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models, schemas
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.enums import ProductStatus
from app.repositories.bids import BidRepository
from app.repositories.product import ProductRepository


def create_bid(
    product_id: int,
    request: schemas.BidCreate,
    db: Session,
    current_user: models.User,
    product_repo: ProductRepository,
    bid_repo: BidRepository,
):

    try:
        product = product_repo.get_by_id_for_update(product_id)

        if not product:
            raise NotFoundError(f"Product with id {product_id} not found")

        if product.status != ProductStatus.ACTIVE:
            raise ConflictError(
                f"Product with id {product_id} is not active for bidding"
            )

        if product.owner_id == current_user.id:
            raise ForbiddenError("Owner of this product cannot place a bid")

        now = datetime.now(UTC)

        if product.auction_ends_at is None or product.auction_ends_at <= now:
            raise ConflictError(f"Auction for product with id {product_id} has ended")
        if request.amount <= product.current_price:
            raise ConflictError(
                f"Bid amount must be greater than the current price of {product.current_price}"
            )

        new_bid = bid_repo.create(
            models.Bids(
                product_id=product_id,
                user_id=current_user.id,
                amount=request.amount,
            )
        )

        product_repo.update(
            product,
            {
                "current_price": request.amount,
            },
        )

        db.commit()
        db.refresh(new_bid)

        return new_bid

    except Exception:
        db.rollback()
        raise
