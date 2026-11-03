from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
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
