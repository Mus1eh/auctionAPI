from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import ForbiddenError, UserNotFoundError
from app.core.policies import has_permission
from app.repositories.user import UserRepository


def get_user_by_id(
    db: Session, user_id: int, user_repo: UserRepository, current_user: models.User
):
    user = user_repo.get_by_id(user_id)

    if not user:
        raise UserNotFoundError()

    if not has_permission(current_user, "user.view_any") and current_user.id != user.id:
        raise ForbiddenError("You cannot access this user's profile.")

    return user
