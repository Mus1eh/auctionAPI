from app import models
from app.core.exceptions import (
    BEARER_CHALLENGE,
    ProductNotFoundError,
    UnauthorizedError,
)
from app.core.policies import is_admin
from app.enums import ProductStatus
from app.repositories.product import ProductRepository

PRIVATE_STATUSES = (
    ProductStatus.DRAFT,
    ProductStatus.REJECTED,
)


def get_product(
    repo: ProductRepository,
    product_id: int,
    current_user: models.User | None,
):
    product = repo.get_by_id(product_id)

    if product is None:
        raise ProductNotFoundError()

    if product.status in PRIVATE_STATUSES:  # noqa
        if current_user is None or (
            not is_admin(current_user) and product.owner_id != current_user.id
        ):
            raise ProductNotFoundError()

    return product


def get_my_product(
    repo: ProductRepository,
    current_user: models.User,
    limit: int,
    offset: int,
) -> tuple[list[models.Product], int]:
    return repo.get_by_owner(current_user.id, limit=limit, offset=offset)


def get_by_status(
    repo: ProductRepository,
    product_status: ProductStatus,
    current_user: models.User | None,
    limit: int,
    offset: int,
):
    # DRAFT AND REJECTED PRODUCTS ARE PRIVATE -> EVERY USER (ADMINS TOO) SEES ONLY THEIR OWN HERE
    # ADMINS SEE EVERYONE'S FROM THE ADMIN DASHBOARD (/admin/products/status/{stat})

    is_private = product_status in PRIVATE_STATUSES

    if is_private and current_user is None:
        raise UnauthorizedError(
            f"Please log in to view your {product_status.value} products.",
            headers=BEARER_CHALLENGE,
        )

    owner_id = current_user.id if is_private and current_user is not None else None

    return repo.get_by_status(
        product_status=product_status, owner_id=owner_id, limit=limit, offset=offset
    )
