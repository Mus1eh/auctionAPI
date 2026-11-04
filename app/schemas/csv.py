from pydantic import BaseModel, ConfigDict, Field


class ProductCSVImport(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    start_price: int = Field(gt=0)

    model_config = ConfigDict(
        extra="forbid"
    )  # Forbid extra fields to ensure correct validation of CSV data.
