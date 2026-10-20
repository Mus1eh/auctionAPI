import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models

load_dotenv()

REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ["REFRESH_TOKEN_EXPIRE_DAYS"])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db_token = models.RefreshToken(
        user_id=user_id, token_hash=hash_token(token), expires_at=expires_at
    )
    db.add(db_token)
    db.flush()
    return token


def verify_refresh_token(db: Session, token: str) -> models.RefreshToken:
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    db_token = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == hash_token(token))
        .first()
    )

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
