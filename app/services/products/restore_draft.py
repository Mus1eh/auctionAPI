from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import (
    ConflictError,
    NotProductOwnerError,
    ProductNotFoundError,
)
from app.enums import ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository


def restore_draft(
    db: Session,
    repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
    product_id: int,
    current_user: models.User,
):
    try:
        product = repo.get_by_id_for_update(product_id)

        if product is None:
            raise ProductNotFoundError()

        if product.owner_id != current_user.id:
            raise NotProductOwnerError()

        if product.status != ProductStatus.REJECTED:
            raise ConflictError("Only rejected products can return to draft.")

        pending_request = status_repo.get_pending_by_product(product.id)

        if pending_request:
            raise ConflictError("Product has a pending status request.")

        repo.update(product, {"status": ProductStatus.DRAFT})

        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise
