from pydantic import BaseModel, ConfigDict, Field

from app.core.limits import INT_MAX
from app.schemas.validator import ProductDescription, ProductName


class ProductCSVImport(BaseModel):
    name: ProductName
    description: ProductDescription | None = None
    start_price: int = Field(gt=0, le=INT_MAX)

    model_config = ConfigDict(
        extra="forbid"
    )  # Forbid extra fields to ensure correct validation of CSV data.
