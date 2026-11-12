from app import models
from app.core.exceptions import BEARER_CHALLENGE, PermissionDeniedError


def has_role(user: models.User, role_name: str) -> bool:
    return any(role.name == role_name for role in user.roles)


def has_permission(user: models.User, permission_name: str) -> bool:
    if has_role(user, "superadmin"):
        return True

    return any(
        permission.name == permission_name
        for role in user.roles
        for permission in role.permissions
    )


# no longer used, but kept for reference
def is_admin(user: models.User) -> bool:
    return any(role.name in {"admin", "superadmin"} for role in user.roles)


def is_superadmin(user: models.User) -> bool:
    return has_role(user, "superadmin")


def require_product_owner_or_permission(
    product: models.Product, current_user: models.User, permission_name: str
) -> None:
    if product.owner_id != current_user.id and not has_permission(
        current_user, permission_name
    ):
        raise PermissionDeniedError(headers=BEARER_CHALLENGE)
