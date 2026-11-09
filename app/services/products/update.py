from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import ConflictError, ProductNotFoundError, UnprocessableError
from app.core.policies import require_product_owner_or_admin
from app.enums import ProductStatus
from app.repositories.product import ProductRepository

EDITABLE_STATUSES = {
    ProductStatus.DRAFT,
    ProductStatus.REJECTED,
}

CLIENT_EDITABLE_FIELDS = {
    "name",
    "description",
    "start_price",
}


def update_product(
    db: Session,
    repo: ProductRepository,
    product_id: int,
    request: dict,
    current_user: models.User,
):
    try:
        # Lock the product while validating and updating.
        product = repo.get_by_id_for_update(product_id)

        if product is None:
            raise ProductNotFoundError()

        # Only the owner or an admin can update.
        require_product_owner_or_admin(
            product,
            current_user,
        )

        # Prevent mass assignment of protected fields.
        unexpected_fields = set(request) - CLIENT_EDITABLE_FIELDS

        if unexpected_fields:
            raise UnprocessableError(
                f"Fields cannot be edited: {sorted(unexpected_fields)}"
            )

        # Prevent edits to active or completed auctions.
        if product.status not in EDITABLE_STATUSES:
            raise ConflictError("This product cannot be edited in its current status.")

        # Check whether the starting price is changing.
        price_changed = (
            "start_price" in request and request["start_price"] != product.start_price
        )

        data = request.copy()

        if price_changed:
            if repo.has_bids(product.id):
                raise ConflictError(
                    "Starting price cannot be changed after bids have been placed."
                )

            if data["start_price"] <= 0:
                raise UnprocessableError("Starting price must be positive.")

            # Internal update, never supplied by the client.
            data["current_price"] = data["start_price"]

        updated_product = repo.update(product, data)

        db.commit()
        db.refresh(updated_product)

        return updated_product

    except Exception:
        db.rollback()
        raise
