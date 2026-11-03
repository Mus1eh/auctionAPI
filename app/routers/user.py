from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_user_repo
from app.oauth2 import get_current_user
from app.repositories.user import UserRepository
from app.services.users.create import create_user as create_user_service
from app.services.users.delete import delete_my_account as delete_my_account_service
from app.services.users.delete import delete_user_by_id as delete_user_by_id_service
from app.services.users.get import get_user_by_id as get_user_by_id_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserShow, status_code=status.HTTP_201_CREATED)
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
):
    return delete_my_account_service(
        db=db,
        current_user=current_user,
        user_repo=user_repo,
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
):
    return delete_user_by_id_service(
        db=db,
        user_id=id,
        current_user=current_user,
        user_repo=user_repo,
    )
