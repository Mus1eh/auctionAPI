from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.enums import ProductStatus
from app.oauth2 import get_current_user

router = APIRouter(prefix="/bids", tags=["Bids"])


@router.post(
    "/{product_id}", response_model=schemas.BidShow, status_code=status.HTTP_201_CREATED
)
def create_bid(
    product_id: int,
    request: schemas.BidCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    try:
        product = (
            db.query(models.Product)
            .filter(models.Product.id == product_id)
            .with_for_update()
            .first()
        )

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

        if current_user.id == product.owner_id:
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

        new_bid = models.Bids(
            product_id=product_id,
            user_id=current_user.id,
            amount=request.increment,
        )

        db.add(new_bid)

        product.current_price = new_bid.amount + product.current_price

        db.commit()
        db.refresh(new_bid)

        return new_bid

    except Exception:
        db.rollback()
        raise


@router.get(
    "/{product_id}",
    response_model=list[schemas.BidShow],
)
def get_bids_for_product(
    product_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=20),
    db: Session = Depends(get_db),
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found",
        )

    bids = (
        db.query(models.Bids)
        .filter(models.Bids.product_id == product_id)
        .order_by(models.Bids.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    if not bids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No bids found for product with id {product_id}",
        )

    return bids
