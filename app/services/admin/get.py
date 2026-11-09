from app import models
from app.enums import ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository


def get_products_by_status(
    repo: ProductRepository,
    product_status: ProductStatus,
    limit: int | None = None,
    offset: int | None = None,
):
    return repo.get_all_by_status(product_status, limit=limit, offset=offset)


def get_pending_status_requests(
    status_repo: ProductStatusRequestRepository,
    limit: int | None = None,
    offset: int | None = None,
) -> tuple[list[models.ProductStatusRequest], int]:
    return status_repo.get_all_pending(limit=limit, offset=offset)
