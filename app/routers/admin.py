from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.dependencies import (
    get_bid_repo,
    get_email_outbox_repo,
    get_product_repo,
    get_product_status_request_repo,
    get_user_repo,
)
from app.enums import ProductStatus
from app.oauth2 import get_current_user
from app.permissions import require_role
from app.repositories.bids import BidRepository
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository
from app.repositories.user import UserRepository
from app.services.admin.approve_status_request import (
    approve_status_request as approve_status_request_service,
)
from app.services.admin.change_role import change_user_role as change_user_role_service
from app.services.admin.change_status import (
    change_product_status as change_product_status_service,
)
from app.services.admin.get import (
    get_pending_status_requests as get_pending_status_requests_service,
)
from app.services.admin.get import (
    get_products_by_status as get_products_by_status_service,
)
from app.services.admin.reject_status_request import (
    reject_status_request as reject_status_request_service,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role(["admin", "superadmin"]))],
)


@router.get("/dashboard")
def admin_dashboard(current_user: models.User = Depends(get_current_user)):
    return {
        "message": "Welcome to the admin dashboard!",
        "username": current_user.username,
        "role": current_user.role_name,
    }


# ADMINS SEE PRODUCTS OF ANY STATUS FROM ALL USERS (INCLUDING DRAFT)
@router.get(
    "/products/status/{stat}",
    response_model=list[schemas.ProductShow],
    response_model_exclude_none=True,
)
def admin_get_products_by_status(
    stat: ProductStatus,
    repo: ProductRepository = Depends(get_product_repo),
):
    return get_products_by_status_service(
        repo=repo,
        product_status=stat,
    )


@router.get(
    "/status-request/pending", response_model=list[schemas.ProductStatusRequestShow]
)
def get_pending_status_request(
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return get_pending_status_requests_service(status_repo=status_repo)


@router.patch(
    "/status-requests/{request_id}/approve",
    response_model=schemas.ProductStatusRequestShow,
)
def approve_status_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return approve_status_request_service(
        db=db,
        product_repo=product_repo,
        status_repo=status_repo,
        request_id=request_id,
        current_user=current_user,
    )


@router.patch(
    "/status-requests/{request_id}/reject",
    response_model=schemas.ProductStatusRequestShow,
)
def reject_status_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return reject_status_request_service(
        db=db,
        product_repo=product_repo,
        status_repo=status_repo,
        request_id=request_id,
        current_user=current_user,
    )


@router.post(
    "/products/{product_id}/status/{status_value}",
    response_model=schemas.ProductShow,
)
def admin_change_product_status(
    product_id: int,
    status_value: ProductStatus,
    db: Session = Depends(get_db),
    product_repo: ProductRepository = Depends(get_product_repo),
    outbox_repo: EmailOutboxRepository = Depends(get_email_outbox_repo),
    bid_repo: BidRepository = Depends(get_bid_repo),
):
    return change_product_status_service(
        db=db,
        product_repo=product_repo,
        product_id=product_id,
        status_value=status_value,
        outbox_repo=outbox_repo,
        bid_repo=bid_repo,
    )


@router.patch(
    "/users/{user_id}/role",
    response_model=schemas.UserShow,
    dependencies=[Depends(require_role(["superadmin"]))],
)
def change_user_role(
    user_id: int,
    request: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    return change_user_role_service(
        user_id=user_id,
        request=request,
        db=db,
        current_user=current_user,
        user_repo=user_repo,
    )
