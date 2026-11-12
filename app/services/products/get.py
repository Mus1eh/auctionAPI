from app import models
from app.core.exceptions import (
    BEARER_CHALLENGE,
    ProductNotFoundError,
    UnauthorizedError,
)
from app.core.policies import has_permission
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
            not has_permission(current_user, "product.view_all")
            and product.owner_id != current_user.id
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
    # DRAFT AND REJECTED PRODUCTS ARE PRIVATE -> USERS SEE ONLY THEIR OWN HERE
    # USERS WITH product.view_all (ADMINS) SEE EVERYONE'S

    is_private = product_status in PRIVATE_STATUSES

    if is_private and current_user is None:
        raise UnauthorizedError(
            f"Please log in to view your {product_status.value} products.",
            headers=BEARER_CHALLENGE,
        )

    owner_id = None
    if (
        is_private
        and current_user is not None
        and not has_permission(current_user, "product.view_all")
    ):
        owner_id = current_user.id

    return repo.get_by_status(
        product_status=product_status, owner_id=owner_id, limit=limit, offset=offset
    )
