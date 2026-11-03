from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.enums import ApprovalStatus, ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository

ALLOWED_TRANSITIONS = {
    ProductStatus.DRAFT: {ProductStatus.ACTIVE},
}


def approve_status_request(
    db: Session,
    product_repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
    request_id: int,
    current_user: models.User,
):
    try:
        # Read request to identify the product.
        status_request = status_repo.get_by_id(request_id)

        if status_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Status request not found.",
            )

        # Lock product first.
        product = product_repo.get_by_id_for_status_change(status_request.product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        # Lock and refresh the status request.
        status_request = status_repo.get_by_id_for_update(request_id)

        if status_request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Status request not found.",
            )

        if status_request.product_id != product.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Status request product has changed.",
            )

        if status_request.approval_status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This status request has already been processed.",
            )

        if status_request.requested_status not in ALLOWED_TRANSITIONS.get(
            product.status, set()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product status has changed. Request cannot be approved.",
            )

        # Activate the auction.
        now = datetime.now(UTC)

        product_repo.update(
            product,
            {
                "status": ProductStatus.ACTIVE,
                "auction_started_at": now,
                "auction_ends_at": now + timedelta(hours=1),
            },
        )

        # Record the admin approval.
        status_repo.update(
            status_request,
            {
                "approval_status": ApprovalStatus.APPROVED,
                "reviewed_by": current_user.id,
                "reviewed_at": now,
            },
        )

        db.commit()
        db.refresh(status_request)

        return status_request

    except Exception:
        db.rollback()
        raise
