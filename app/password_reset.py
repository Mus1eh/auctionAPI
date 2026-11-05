import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import settings
from app.refresh_token import hash_token
from app.repositories.authentication import AuthenticationRepository


def create_password_reset_token(
    auth_repo: AuthenticationRepository, user_id: int
) -> str:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.reset_password_token_expire_minutes,
    )

    auth_repo.create_password_reset_token(user_id, hash_token(token), expires_at)
    return token


def verify_password_reset_token(auth_repo: AuthenticationRepository, token: str):
    db_token = auth_repo.get_password_reset_token_by_hash(hash_token(token))

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token",
        )
    if db_token.used_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has already been used",
        )
    if db_token.expires_at <= datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired",
        )
    return db_token
