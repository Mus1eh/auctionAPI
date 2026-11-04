from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.authentication import AuthenticationRepository
from app.repositories.bids import BidRepository
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
