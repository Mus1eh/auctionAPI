from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.enums import ProductStatus
from app.permissions import require_product_owner_or_admin
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository

DELETABLE_STATUSES = (
    ProductStatus.DRAFT,
    ProductStatus.REJECTED,
    ProductStatus.CLOSED,
)


def delete_product(
    db: Session,
    repo: ProductRepository,
    product_id: int,
    current_user: models.User,
    status_repo: ProductStatusRequestRepository,
):
    # Lock the product while validating and deleting.
    product = repo.get_by_id_for_update(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    require_product_owner_or_admin(product, current_user)

    if product.status not in DELETABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product cannot be deleted in its current status.",
        )

    if repo.has_bids(product_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product cannot be deleted because it has bids.",
        )

    pending_request = status_repo.get_pending_by_product(product_id)

    try:
        if pending_request:
            status_repo.cancel(pending_request, current_user.id)

        repo.softdelete(product)
        db.commit()

        return {"detail": "Product deleted successfully."}

    except Exception:
        db.rollback()
        raise
