from app import models
from app.repositories.bids import BidRepository
from app.repositories.product import ProductRepository
from app.services.products.get import get_product


def get_bids_for_product(
    product_id: int,
    page: int,
    limit: int,
    product_repo: ProductRepository,
    bid_repo: BidRepository,
    current_user: models.User | None,
):
    # Raises 404 if the product is missing or private to someone else.
    get_product(
        repo=product_repo,
        product_id=product_id,
        current_user=current_user,
    )

    return bid_repo.get_bids_for_product(product_id, page, limit)
