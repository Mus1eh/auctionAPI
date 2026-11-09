from pydantic import BaseModel, EmailStr, Field

from app.core.limits import EMAIL_MAX, PASSWORD_MAX, PASSWORD_MIN


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(max_length=EMAIL_MAX)


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)


class ResetPasswordToken(BaseModel):
    reset_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
