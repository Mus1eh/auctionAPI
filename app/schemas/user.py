import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.limits import (
    EMAIL_MAX,
    PASSWORD_MAX,
    PASSWORD_MIN,
    USERNAME_MAX,
    USERNAME_MIN,
)


class UserCreate(BaseModel):
    username: str = Field(min_length=USERNAME_MIN, max_length=USERNAME_MAX)
    email: EmailStr = Field(max_length=EMAIL_MAX)
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError("Invalid username.")

        return value


class UserShow(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserRestore(BaseModel):
    email: EmailStr = Field(max_length=EMAIL_MAX)


class UserRestoreConfirm(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class UserDetail(UserShow):
    roles: list[str]

    @field_validator("roles", mode="before")
    @classmethod
    def role_names(cls, value):
        return sorted(getattr(role, "name", role) for role in value)


class UserMe(UserDetail):
    permissions: list[str]
