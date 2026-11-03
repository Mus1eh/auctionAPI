from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.permissions import is_admin, is_superadmin
from app.repositories.user import UserRepository


def delete_my_account(
    db: Session, current_user: models.User, user_repo: UserRepository
):

    if is_superadmin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin accounts cannot be deleted.",
        )
    try:
        user_repo.softdelete(current_user)
        db.commit()

        return {"message": "Your account has been successfully deleted."}
    except Exception:
        db.rollback()
        raise


def delete_user_by_id(
    db: Session,
    user_id: int,
    current_user: models.User,
    user_repo: UserRepository,
):
    # Lock the user while validating and deleting.
    user_to_delete = user_repo.get_by_id_for_delete(user_id)
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not found.",
        )

    is_self = current_user.id == user_to_delete.id
    allowed = False

    if is_superadmin(user_to_delete):
        allowed = False
    elif is_self:
        allowed = True
    elif user_to_delete.role_name == "admin":
        allowed = is_superadmin(current_user)
    elif user_to_delete.role_name == "user":
        allowed = is_admin(current_user)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )
    try:
        user_repo.softdelete(user_to_delete)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "User deleted successfully."}
