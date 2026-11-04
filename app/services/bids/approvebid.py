from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.email_templates import bid_approved_email, bid_rejected_email
from app.enums import ApproveBidding, ProductStatus
from app.permissions import is_superadmin
from app.repositories.bids import BidRepository
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.product import ProductRepository

ALLOWED_APPROVE_STATUSES = (ProductStatus.CLOSED, ProductStatus.REJECTED)


def approve_bid(
    product_id: int,
    request: ApproveBidding,
    bid_repo: BidRepository,
    product_repo: ProductRepository,
    outbox_repo: EmailOutboxRepository,
    current_user: models.User,
    db: Session,
):
    try:
        product = product_repo.get_by_id_for_update(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {product_id} not found",
            )

        if product.owner_id != current_user.id and not is_superadmin(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the owner or a superadmin can approve or reject bids",
            )

        if product.status == ProductStatus.SOLD:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bidding has already been approved for this product.",
            )

        if product.status not in ALLOWED_APPROVE_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only closed or rejected products can be approved or rejected.",
            )

        highest_bid = bid_repo.get_highest_by_product(product_id)

        if not highest_bid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No bids found for this product.",
            )

        winning_bidder = None

        if request == ApproveBidding.APPROVE:
            product.status = ProductStatus.SOLD
            product.winning_bid_id = highest_bid.id

            winning_bidder = {
                "id": highest_bid.bidder.id,
                "username": highest_bid.bidder.username,
            }

            outbox_repo.create(
                to_email=highest_bid.bidder.email,
                subject=f"Bid Approved - Product #{product.id}",
                body=bid_approved_email(
                    product,
                    highest_bid.bidder,
                ),
            )

        elif request == ApproveBidding.REJECT:
            product.status = ProductStatus.REJECTED
            product.winning_bid_id = None

            outbox_repo.create(
                to_email=highest_bid.bidder.email,
                subject=f"Bid Rejected - Product #{product.id}",
                body=bid_rejected_email(
                    product,
                    highest_bid.bidder,
                ),
            )

        result = {
            **schemas.ProductShow.model_validate(product).model_dump(),
            "winning_bidder": winning_bidder,
        }

        db.commit()

        return result

    except Exception:
        db.rollback()
        raise
