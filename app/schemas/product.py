from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums import ProductStatus


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str | None = None
    start_price: int = Field(gt=0)


class ProductShow(BaseModel):
    id: int
    name: str
    description: str | None = None
    start_price: int
    current_price: int
    owner_id: int
    status: ProductStatus

    auction_started_at: datetime | None = None
    auction_ends_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    start_price: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_patch(self):
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Name cannot be None when provided.")
        if "start_price" in self.model_fields_set and self.start_price is None:
            raise ValueError("Start price cannot be None when provided.")
        return self


class GetProductByStatus(BaseModel):
    status: ProductStatus
