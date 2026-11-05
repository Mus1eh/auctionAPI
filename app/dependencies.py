from functools import lru_cache

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import RateLimiter
from app.repositories.authentication import AuthenticationRepository
from app.repositories.bids import BidRepository
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository
from app.repositories.user import UserRepository


def get_product_repo(db: Session = Depends(get_db)) -> ProductRepository:
    return ProductRepository(db)


def get_product_status_request_repo(
    db: Session = Depends(get_db),
) -> ProductStatusRequestRepository:
    return ProductStatusRequestRepository(db)


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_bid_repo(db: Session = Depends(get_db)) -> BidRepository:
    return BidRepository(db)


def get_auth_repo(db: Session = Depends(get_db)) -> AuthenticationRepository:
    return AuthenticationRepository(db)


def get_email_outbox_repo(db: Session = Depends(get_db)) -> EmailOutboxRepository:
    return EmailOutboxRepository(db)


# Rate limiter is cached so we use the same instance of all requests
@lru_cache
def get_rate_limiter() -> RateLimiter:
    return RateLimiter(settings.rate_limit_storage)


# getting client IP address
def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# limiting requests by IP address
def limit_by_ip(scope: str, rule: str):
    def dependency(
        request: Request, limiter: RateLimiter = Depends(get_rate_limiter)
    ) -> None:
        limiter.check(scope, client_ip(request), rule)

    return dependency
