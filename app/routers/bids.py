from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.enums import ApproveBidding, ProductStatus
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

    return bids


@router.post(
    "/{product_id}/approve",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ProductApprovalShow,
)
def approve_bid(
    product_id: int,
    request: ApproveBidding,
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

        if product.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner of the product can approve or reject bids",
            )

        if product.status == ProductStatus.SOLD:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bidding has already been approved for this product.",
            )

        if product.status not in (
            ProductStatus.CLOSED,
            ProductStatus.REJECTED,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only closed or rejected products can be approved or rejected.",
            )

        latest_bid = (
            db.query(models.Bids)
            .filter(models.Bids.product_id == product_id)
            .order_by(models.Bids.id.desc())
            .first()
        )

        if not latest_bid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No bids found for this product.",
            )

        # if owner accpets status -> sold if not status -> closed
        winning_bidder = None

        if request == ApproveBidding.APPROVE:
            product.status = ProductStatus.SOLD
            product.winning_bid_id = latest_bid.id

            winning_bidder = {
                "id": latest_bid.bidder.id,
                "username": latest_bid.bidder.username,
            }

        elif request == ApproveBidding.REJECT:
            product.status = ProductStatus.REJECTED
            product.winning_bid_id = None

        result = {
            **schemas.ProductShow.model_validate(product).model_dump(),
            "winning_bidder": winning_bidder,
        }

        db.commit()

        return result

    except Exception:
        db.rollback()
        raise
