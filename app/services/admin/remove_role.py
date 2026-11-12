from sqlalchemy.orm import Session

from app import models
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UserNotFoundError,
)
from app.repositories.user import UserRepository


def remove_user_role(
    db: Session,
    user_id: int,
    role_name: str,
    current_user: models.User,
    user_repo: UserRepository,
):
    try:
        if role_name == "superadmin":
            raise ForbiddenError("You cannot remove the superadmin role.")

        user = user_repo.get_by_id_for_update(user_id)

        if user is None:
            raise UserNotFoundError()

        if current_user.id == user_id and role_name == "admin":
            raise BadRequestError("You cannot remove your own admin role.")

        role = user_repo.get_role_by_name(role_name)

        if role is None:
            raise NotFoundError("Role is not found.")

        if not user_repo.has_role(user, role_name):
            raise ConflictError("The user does not have this role.")

        if len(user.roles) <= 1:
            raise BadRequestError("The user must have at least one role.")

        user_repo.remove_role(user, role)

        db.commit()
        db.refresh(user)

        return user
    except Exception:
        db.rollback()
        raise
