from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.hashing import Hash
from app.permissions import is_admin
from app.repositories.user import UserRepository


def create_user(db: Session, request: schemas.UserCreate, user_repo: UserRepository):

    existing_user = user_repo.check_user_exists(
        username=request.username,
        email=request.email,
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or Email already exists.",
        )

    try:
        new_user = models.User(
            username=request.username,
            email=request.email,
            password=Hash.crypt_password(request.password),
            role_name="user",
        )

        user_repo.create(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception:
        db.rollback()
        raise


def get_user_by_id(
    db: Session, user_id: int, user_repo: UserRepository, current_user: models.User
):
    user = user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User is not found."
        )

    if not is_admin(current_user) and current_user.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this user's profile.",
        )

    return user
