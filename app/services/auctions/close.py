from sqlalchemy.orm import Session

from app import models
from app.email_templates import (
    highest_bidder_email,
    owner_auction_closed_email,
)
from app.enums import ProductStatus
from app.repositories.bids import BidRepository
from app.repositories.email_outbox import EmailOutboxRepository


def close_auction(
    db: Session,
    product: models.Product,
    outbox_repo: EmailOutboxRepository,
    bid_repo: BidRepository,
) -> None:
    if product.status != ProductStatus.ACTIVE:
        raise ValueError("Only active auctions can be closed")

    bids_count = bid_repo.count_by_product(product.id)

    latest_bid = bid_repo.get_latest_by_product(product.id)

    auction = {
        "product_id": product.id,
        "product_name": product.name,
        "owner_email": product.owner.email,
        "auction_started_at": product.auction_started_at,
        "auction_ends_at": product.auction_ends_at,
        "bids_count": bids_count,
        "last_price": product.current_price,
        "highest_bidder_email": latest_bid.bidder.email if latest_bid else None,
        "highest_bidder_username": latest_bid.bidder.username if latest_bid else None,
    }

    product.status = ProductStatus.CLOSED

    outbox_repo.create(
        to_email=auction["owner_email"],
        subject=f"Auction Closed - Product #{product.id}",
        body=owner_auction_closed_email(auction),
    )

    if auction["highest_bidder_email"]:
        outbox_repo.create(
            to_email=auction["highest_bidder_email"],
            subject=f"Highest Bid - Product #{product.id}",
            body=highest_bidder_email(auction),
        )
