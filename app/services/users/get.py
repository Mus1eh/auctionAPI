from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import ForbiddenError, UserNotFoundError
from app.core.policies import is_admin
from app.repositories.user import UserRepository


def get_user_by_id(
    db: Session, user_id: int, user_repo: UserRepository, current_user: models.User
):
    user = user_repo.get_by_id(user_id)

    if not user:
        raise UserNotFoundError()

    if not is_admin(current_user) and current_user.id != user.id:
        raise ForbiddenError("You cannot access this user's profile.")

    return user
