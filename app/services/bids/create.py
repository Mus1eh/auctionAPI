from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found",
            )

        if product.status != ProductStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with id {product_id} is not active for bidding",
            )

        if product.owner_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Owner of this product cannot place a bid",
            )

        now = datetime.now(UTC)

        if product.auction_ends_at is None or product.auction_ends_at <= now:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Auction for product with id {product_id} has ended",
            )
        if request.amount <= product.current_price:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Bid amount must be greater than the current price of {product.current_price}",
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
