from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models
from app.enums import ApprovalStatus

ALLOWED_FIELDS = {
    "approval_status",
    "reviewed_by",
    "reviewed_at",
}


class ProductStatusRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_pending_by_product(self, product_id: int):
        return (
            self.db.query(models.ProductStatusRequest)
            .filter(
                models.ProductStatusRequest.product_id == product_id,
                models.ProductStatusRequest.approval_status == ApprovalStatus.PENDING,
            )
            .first()
        )

    def cancel(self, status_request: models.ProductStatusRequest, reviewed_by: int):
        return self.update(
            status_request,
            {
                "approval_status": ApprovalStatus.CANCELLED,
                "reviewed_by": reviewed_by,
                "reviewed_at": datetime.now(UTC),
            },
        )

    def get_all_pending(self):
        return (
            self.db.query(models.ProductStatusRequest)
            .filter(
                models.ProductStatusRequest.approval_status == ApprovalStatus.PENDING
            )
            .order_by(models.ProductStatusRequest.created_at.asc())
            .all()
        )

    def create(self, status_request: models.ProductStatusRequest):
        self.db.add(status_request)
        self.db.flush()
        return status_request

    def update(self, status_request: models.ProductStatusRequest, data: dict):
        for key, value in data.items():
            if key not in ALLOWED_FIELDS:
                raise ValueError(f"Field '{key}' is not allowed to be updated.")
            setattr(status_request, key, value)

        self.db.flush()
        return status_request

    def get_by_id(self, request_id: int):
        return (
            self.db.query(models.ProductStatusRequest)
            .filter(models.ProductStatusRequest.id == request_id)
            .first()
        )

    def get_by_id_for_update(self, request_id: int):
        return (
            self.db.query(models.ProductStatusRequest)
            .filter(models.ProductStatusRequest.id == request_id)
            .with_for_update()
            .populate_existing()
            .first()
        )
