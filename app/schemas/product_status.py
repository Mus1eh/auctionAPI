from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums import ApprovalStatus, ProductStatus


class ProductStatusRequestShow(BaseModel):
    id: int
    product_id: int
    requested_by: int
    requested_status: ProductStatus
    approval_status: ApprovalStatus
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by: int | None = None

    model_config = ConfigDict(from_attributes=True)
