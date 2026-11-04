from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.permissions import is_superadmin
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to change user roles.",
            )

        if request.role_name not in ["admin", "user"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only user and admin roles can be assigned.",
            )

        user = user_repo.get_by_id_for_delete(user_id)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if is_superadmin(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot change the role of a superadmin.",
            )

        if user.role_name == request.role_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The user already has this role.",
            )

        role = user_repo.get_role_by_name(request.role_name)

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found.",
            )

        new_user_role = user_repo.update_role(user, role)

        db.commit()
        db.refresh(new_user_role)
        return new_user_role

    except Exception:
        db.rollback()
        raise
