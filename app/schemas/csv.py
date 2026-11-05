from pydantic import BaseModel, ConfigDict, Field

from app.core.limits import INT_MAX, PRODUCT_DESCRIPTION_MAX, PRODUCT_NAME_MAX


class ProductCSVImport(BaseModel):
    name: str = Field(min_length=1, max_length=PRODUCT_NAME_MAX)
    description: str | None = Field(default=None, max_length=PRODUCT_DESCRIPTION_MAX)
    start_price: int = Field(gt=0, le=INT_MAX)

    model_config = ConfigDict(
        extra="forbid"
    )  # Forbid extra fields to ensure correct validation of CSV data.
