from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.security import Hash
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
