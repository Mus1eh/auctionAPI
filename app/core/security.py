from datetime import UTC, datetime, timedelta

from jose import jwt
from pwdlib import PasswordHash

from app.core.config import settings


class Hash:
    def crypt_password(password: str) -> str:
        # password hashing using recommended algorithm from pwdlib
        pwd_context = PasswordHash.recommended()
        return pwd_context.hash(password)

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # password verification using the plain and hashed password
        pwd_context = PasswordHash.recommended()
        return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    # create JWT access token with expiration time
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )

    return encoded_jwt
