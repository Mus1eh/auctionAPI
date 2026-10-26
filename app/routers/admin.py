from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.enums import ApprovalStatus, ProductStatus
from app.oauth2 import get_current_user
from app.permissions import require_role
from app.services.auction_service import close_auction

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


@router.get(
    "/status-request/pending", response_model=list[schemas.ProductStatusRequestShow]
)
def get_pending_status_request(
    db: Session = Depends(get_db),
):
    pending_requests = (
        db.query(models.ProductStatusRequest)
        .filter(models.ProductStatusRequest.approval_status == "pending")
        .order_by(models.ProductStatusRequest.created_at.asc())
        .all()
    )

    return pending_requests


@router.patch(
    "/status-requests/{request_id}/approve",
    response_model=schemas.ProductStatusRequestShow,
)
def approve_status_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        status_request = (
            db.query(models.ProductStatusRequest)
            .filter(models.ProductStatusRequest.id == request_id)
            .first()
        )

        if not status_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Status request not found.",
            )

        product = (
            db.query(models.Product)
            .filter(models.Product.id == status_request.product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        status_request = (
            db.query(models.ProductStatusRequest)
            .filter(models.ProductStatusRequest.id == request_id)
            .with_for_update()
            .populate_existing()
            .first()
        )

        if status_request.approval_status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This status request has already been processed.",
            )

        allowed_transitions = {
            ProductStatus.DRAFT: {ProductStatus.ACTIVE},
            ProductStatus.ACTIVE: {ProductStatus.CLOSED},
        }

        if status_request.requested_status not in allowed_transitions.get(
            product.status, set()
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The product status has been changed, This request cannot be approved.",
            )

        # with_for_update() ensure that the product row is locked for the duration of the transaciton,
        # preventing other transactions from modifying it until current transaction is complete
        # preventing multiple admins from approving the same request simultaneously and causing data inconsistencies

        product.status = status_request.requested_status

        if product.status == ProductStatus.ACTIVE:
            product.auction_started_at = datetime.now(UTC)
            product.auction_ends_at = datetime.now(UTC) + timedelta(hours=1)

        status_request.approval_status = ApprovalStatus.APPROVED
        status_request.reviewed_by = current_user.id
        status_request.reviewed_at = datetime.now(UTC)

        db.commit()
        db.refresh(status_request)

        return status_request

    except Exception:
        db.rollback()
        raise


@router.patch(
    "/status-requests/{request_id}/reject",
    response_model=schemas.ProductStatusRequestShow,
)
def reject_status_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        status_request = (
            db.query(models.ProductStatusRequest)
            .filter(models.ProductStatusRequest.id == request_id)
            .first()
        )

        if not status_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Status request not found.",
            )

        product = (
            db.query(models.Product)
            .filter(models.Product.id == status_request.product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        status_request = (
            db.query(models.ProductStatusRequest)
            .filter(models.ProductStatusRequest.id == request_id)
            .with_for_update()
            .populate_existing()
            .first()
        )

        if status_request.approval_status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This status request has already been processed.",
            )

        status_request.approval_status = ApprovalStatus.REJECTED
        status_request.reviewed_by = current_user.id
        status_request.reviewed_at = datetime.now(UTC)

        db.commit()
        db.refresh(status_request)

    except Exception:
        db.rollback()
        raise

    return status_request


@router.post(
    "/products/{product_id}/status/{status_value}",
    response_model=schemas.ProductShow,
)
def admin_change_product_status(
    product_id: int,
    status_value: ProductStatus,
    db: Session = Depends(get_db),
):
    try:
        product = (
            db.query(models.Product)
            .filter(models.Product.id == product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        if product.status == status_value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Product is already in the requested status.",
            )

        if status_value == ProductStatus.CLOSED:
            if product.status != ProductStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only active auctions can be closed.",
                )

            close_auction(db, product)

        elif status_value == ProductStatus.ACTIVE:
            if product.status != ProductStatus.DRAFT:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only draft products can be activated.",
                )

            now = datetime.now(UTC)

            product.status = ProductStatus.ACTIVE
            product.auction_started_at = now
            product.auction_ends_at = now + timedelta(hours=1)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint supports activating or closing auctions only.",
            )

        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise


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
):
    try:
        if request.role_name not in ("user", "admin"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only 'user' and 'admin' roles can be assigned",
            )

        user = (
            db.query(models.User)
            .filter(models.User.id == user_id)
            .with_for_update()
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.role_name == "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify a superadmin account",
            )

        role = (
            db.query(models.Role).filter(models.Role.name == request.role_name).first()
        )

        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        user.role_name = role.name

        db.commit()
        db.refresh(user)

        return user

    except Exception:
        db.rollback()
        raise
