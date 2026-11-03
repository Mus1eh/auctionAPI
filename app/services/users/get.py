from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.permissions import is_admin
from app.repositories.user import UserRepository


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
