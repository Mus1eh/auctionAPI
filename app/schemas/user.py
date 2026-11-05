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
        if "@" in value:
            raise ValueError("Username cannot contain '@'")
        return value


class UserShow(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
