import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status

from app import models
from app.config import settings
from app.repositories.authentication import AuthenticationRepository


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(auth_repo: AuthenticationRepository, user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)

    auth_repo.create_refresh_token(user_id, hash_token(token), expires_at)
    return token


def verify_refresh_token(
    auth_repo: AuthenticationRepository, token: str
) -> models.RefreshToken:
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    db_token = auth_repo.get_refresh_token_by_hash(hash_token(token))

    if not db_token:
        raise unauthorized_exception
    if db_token.revoked_at is not None:
        raise unauthorized_exception

    expires_at = db_token.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < datetime.now(UTC):
        raise unauthorized_exception
    return db_token
