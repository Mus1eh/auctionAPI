import os
import secrets
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.refresh_token import hash_token

load_dotenv()

RESET_PASSWORD_TOKEN_EXPIRE_MINUTES = int(
    os.environ["RESET_PASSWORD_TOKEN_EXPIRE_MINUTES"]
)


def create_password_reset_token(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(UTC) + timedelta(
        minutes=RESET_PASSWORD_TOKEN_EXPIRE_MINUTES
    )

    db_token = models.PasswordResetToken(
        user_id=user_id, token_hash=hash_token(token), expires_at=expires_at
    )

    db.add(db_token)
    db.flush()
    return token


def verify_password_reset_token(db: Session, token: str):
    token_hash = hash_token(token)

    db_token = (
        db.query(models.PasswordResetToken)
        .filter(models.PasswordResetToken.token_hash == token_hash)
        .first()
    )

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
