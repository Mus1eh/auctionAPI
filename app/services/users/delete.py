from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.core.policies import is_admin, is_superadmin
from app.enums import ProductStatus
from app.repositories.authentication import AuthenticationRepository
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository
from app.repositories.user import UserRepository

# Only the owner can approve the highest bid, so these must be settled first.
UNSETTLED_AUCTION_STATUSES = (ProductStatus.ACTIVE, ProductStatus.CLOSED)


def _delete_owned_products(
    owner_id: int,
    deleted_by: int,
    product_repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
):
    # Lock the products so no bid can be placed while checking them.
    for product in product_repo.get_by_owner_for_update(owner_id):
        if product_repo.has_bids(product.id):
            if product.status in UNSETTLED_AUCTION_STATUSES:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        "This account has auctions with bids that are not settled yet."
                    ),
                )

            # Products with bids stay for history.
            continue

        pending_request = status_repo.get_pending_by_product(product.id)

        if pending_request:
            status_repo.cancel(pending_request, deleted_by)

        product_repo.softdelete(product)


def delete_my_account(
    db: Session,
    current_user: models.User,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
    product_repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
):

    if is_superadmin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin accounts cannot be deleted.",
        )
    try:
        _delete_owned_products(
            owner_id=int(current_user.id),
            deleted_by=int(current_user.id),
            product_repo=product_repo,
            status_repo=status_repo,
        )
        user_repo.softdelete(current_user)
        auth_repo.revoke_all_refresh_token_by_user_id(int(current_user.id))
        auth_repo.revoke_all_password_reset_token_by_user_id(int(current_user.id))
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
    auth_repo: AuthenticationRepository,
    product_repo: ProductRepository,
    status_repo: ProductStatusRequestRepository,
):
    # Lock the user while validating and deleting.
    user_to_delete = user_repo.get_by_id_for_update(user_id)
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
        _delete_owned_products(
            owner_id=int(user_to_delete.id),
            deleted_by=int(current_user.id),
            product_repo=product_repo,
            status_repo=status_repo,
        )
        user_repo.softdelete(user_to_delete)
        auth_repo.revoke_all_refresh_token_by_user_id(int(user_to_delete.id))
        auth_repo.revoke_all_password_reset_token_by_user_id(int(user_to_delete.id))
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "User deleted successfully."}
