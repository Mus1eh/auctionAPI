from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.enums import ProductStatus
from app.permissions import require_product_owner_or_admin
from app.repositories.product import ProductRepository

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
):
    # Lock the product while validating and deleting.
    product = repo.get_by_id_for_delete(product_id)

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

    try:
        repo.softdelete(product)
        db.commit()

    except Exception:
        db.rollback()
        raise
