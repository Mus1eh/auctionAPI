from fastapi import Depends, HTTPException, status

from app import models
from app.oauth2 import get_current_user


def require_role(allowd_roles: list[str]):
    def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.role_name not in allowd_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return role_checker


def require_product_owner_or_admin(
    product: models.Product, current_user: models.User = Depends(get_current_user)
):
    if product.owner_id != current_user.id and current_user.role_name not in [
        "admin",
        "superadmin",
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
            headers={"WWW-Authenticate": "Bearer"},
        )
