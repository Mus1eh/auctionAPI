from fastapi import Depends

from app import models
from app.core.exceptions import PermissionDeniedError
from app.oauth2 import get_current_user


# old code
def require_role(allowed_roles: list[str]):
    def role_checker(
        current_user: models.User = Depends(get_current_user),
    ):
        user_roles = {role.name for role in current_user.roles}

        if not user_roles.intersection(allowed_roles):
            raise PermissionDeniedError()

        return current_user

    return role_checker


def require_permission(permission_name: str):
    def permission_checker(
        current_user: models.User = Depends(get_current_user),
    ):
        # Superadmin bypass
        if any(role.name == "superadmin" for role in current_user.roles):
            return current_user

        # permissions from all assigned roles
        user_permissions = {
            permission.name
            for role in current_user.roles
            for permission in role.permissions
        }

        if permission_name not in user_permissions:
            raise PermissionDeniedError()

        return current_user

    return permission_checker
