from fastapi import Depends

from app import models
from app.core.exceptions import PermissionDeniedError
from app.oauth2 import get_current_user


def require_role(allowd_roles: list[str]):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role_name not in allowd_roles:
            raise PermissionDeniedError()
        return current_user

    return role_checker
