from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.dependencies import (
    get_auth_repo,
    get_product_repo,
    get_product_status_request_repo,
    get_user_repo,
    limit_by_ip,
)
from app.oauth2 import get_current_user
from app.repositories.authentication import AuthenticationRepository
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository
from app.repositories.user import UserRepository
from app.services.users.create import create_user as create_user_service
from app.services.users.delete import delete_my_account as delete_my_account_service
from app.services.users.delete import delete_user_by_id as delete_user_by_id_service
from app.services.users.get import get_user_by_id as get_user_by_id_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/",
    response_model=schemas.UserShow,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_by_ip("register", "5/hour"))],
)
def create_user(
    request: schemas.UserCreate,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
):
    return create_user_service(db=db, request=request, user_repo=user_repo)


# DELETE MY OWN ACCOUNT -> MUST BE ABOVE "/{id}" ROUTES SO "me" ISN'T PARSED AS AN ID
@router.delete("/me", status_code=status.HTTP_202_ACCEPTED)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return delete_my_account_service(
        db=db,
        current_user=current_user,
        user_repo=user_repo,
        auth_repo=auth_repo,
        product_repo=product_repo,
        status_repo=status_repo,
    )


@router.get("/me", response_model=schemas.UserShow)
def get_my_account(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


@router.get("/{id}", response_model=schemas.UserShow)
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    return get_user_by_id_service(
        db=db, user_id=id, user_repo=user_repo, current_user=current_user
    )


@router.delete("/{id}", status_code=status.HTTP_202_ACCEPTED)
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return delete_user_by_id_service(
        db=db,
        user_id=id,
        current_user=current_user,
        user_repo=user_repo,
        auth_repo=auth_repo,
        product_repo=product_repo,
        status_repo=status_repo,
    )
