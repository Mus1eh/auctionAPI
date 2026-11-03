from app.enums import ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository


def get_products_by_status(
    repo: ProductRepository,
    product_status: ProductStatus,
):
    return repo.get_all_by_status(product_status)


def get_pending_status_requests(
    status_repo: ProductStatusRequestRepository,
):
    return status_repo.get_all_pending()
