from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.enums import ApprovalStatus, ProductStatus


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


class UserShow(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    start_price: int = Field(gt=0)


class ProductShow(BaseModel):
    id: int
    name: str
    description: str | None = None
    start_price: int
    owner_id: int
    status: ProductStatus

    model_config = ConfigDict(from_attributes=True)


class GetProductByStatus(BaseModel):
    status: ProductStatus


class ProductPatch(BaseModel):
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


class RoleShow(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ResetPasswordToken(BaseModel):
    reset_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class ProductStatusUpdate(BaseModel):
    status: ProductStatus


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
