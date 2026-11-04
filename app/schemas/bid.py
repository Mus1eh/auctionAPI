from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums import ApproveBidding
from app.schemas.product import ProductShow


class BidCreate(BaseModel):
    amount: int = Field(gt=0)


class BidShow(BaseModel):
    id: int
    product_id: int
    user_id: int
    amount: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApproveBidRequest(BaseModel):
    action: ApproveBidding


class LastBidderShow(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ProductApprovalShow(ProductShow):
    winning_bidder: LastBidderShow | None = None
