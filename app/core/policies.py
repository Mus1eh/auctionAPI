from app import models
from app.core.exceptions import BEARER_CHALLENGE, PermissionDeniedError


def is_admin(user: models.User) -> bool:
    return user.role_name in ["admin", "superadmin"]


def is_superadmin(user: models.User) -> bool:
    return user.role_name == "superadmin"


def require_product_owner_or_admin(
    product: models.Product, current_user: models.User
) -> None:
    if product.owner_id != current_user.id and not is_admin(current_user):
        raise PermissionDeniedError(headers=BEARER_CHALLENGE)
