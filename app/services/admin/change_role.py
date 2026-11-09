from sqlalchemy.orm import Session

from app import models, schemas
from app.core.exceptions import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UserNotFoundError,
)
from app.core.policies import is_superadmin
from app.repositories.user import UserRepository


def change_user_role(
    user_id: int,
    request: schemas.UserRoleUpdate,
    db: Session,
    current_user: models.User,
    user_repo: UserRepository,
):
    try:
        if not is_superadmin(current_user):
            raise ForbiddenError("You do not have permission to change user roles.")

        if request.role_name not in ["admin", "user"]:
            raise BadRequestError("Only user and admin roles can be assigned.")

        user = user_repo.get_by_id_for_update(user_id)

        if user is None:
            raise UserNotFoundError()

        if is_superadmin(user):
            raise ForbiddenError("You cannot change the role of a superadmin.")

        if user.role_name == request.role_name:
            raise ConflictError("The user already has this role.")

        role = user_repo.get_role_by_name(request.role_name)

        if not role:
            raise NotFoundError("Role is not found.")

        new_user_role = user_repo.update_role(user, role)

        db.commit()
        db.refresh(new_user_role)
        return new_user_role

    except Exception:
        db.rollback()
        raise
