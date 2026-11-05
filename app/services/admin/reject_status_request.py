from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import (
    ConflictError,
    ProductNotFoundError,
    StatusRequestAlreadyProcessedError,
    StatusRequestNotFoundError,
    StatusRequestProductChangedError,
)
from app.enums import ApprovalStatus, ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository


def reject_status_request(
    db: Session,
    product_repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
    request_id: int,
    current_user: models.User,
):
    try:
        status_request = status_repo.get_by_id(request_id)

        if status_request is None:
            raise StatusRequestNotFoundError()

        product = product_repo.get_by_id_for_update(status_request.product_id)

        if product is None:
            raise ProductNotFoundError()

        status_request = status_repo.get_by_id_for_update(request_id)

        if status_request is None:
            raise StatusRequestNotFoundError()

        if status_request.product_id != product.id:
            raise StatusRequestProductChangedError()

        if status_request.approval_status != ApprovalStatus.PENDING:
            raise StatusRequestAlreadyProcessedError()

        if (
            product.status != ProductStatus.DRAFT
            or status_request.requested_status != ProductStatus.ACTIVE
        ):
            raise ConflictError(
                "Product status has changed. Request cannot be rejected."
            )

        now = datetime.now(UTC)

        product_repo.update(product, {"status": ProductStatus.REJECTED})

        status_repo.update(
            status_request,
            {
                "approval_status": ApprovalStatus.REJECTED,
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
