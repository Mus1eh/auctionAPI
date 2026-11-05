from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotProductOwnerError,
    ProductNotFoundError,
    SameStatusError,
)
from app.enums import ApprovalStatus, ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository

ALLOWED_TRANSITIONS = {
    ProductStatus.DRAFT: {ProductStatus.ACTIVE},
}


def request_status_change(
    db: Session,
    repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
    product_id: int,
    request: ProductStatus,
    current_user: models.User,
):
    try:
        product = repo.get_by_id_for_update(product_id)

        if not product:
            raise ProductNotFoundError()

        if product.owner_id != current_user.id:
            raise NotProductOwnerError()

        pending_request = status_repo.get_pending_by_product(product.id)

        if pending_request:
            raise ConflictError("There is already a pending request for this product.")

        if request == product.status:
            raise SameStatusError()

        if request == ProductStatus.CLOSED:
            raise ForbiddenError(
                "You cannot request to close the product, please wait until the timer runs out."
            )

        if request not in ALLOWED_TRANSITIONS.get(product.status, set()):
            raise ConflictError("Invalid product status transition.")

        new_request = models.ProductStatusRequest(
            product_id=product.id,
            requested_status=request,
            approval_status=ApprovalStatus.PENDING,
            requested_by=current_user.id,
        )

        status_repo.create(new_request)
        db.commit()
        db.refresh(new_request)

        return new_request
    except Exception:
        db.rollback()
        raise
