import secrets
from datetime import UTC, datetime, timedelta

from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    InvalidResetTokenError,
    ResetTokenAlreadyUsedError,
)
from app.repositories.authentication import AuthenticationRepository
from app.services.authentication.refresh_tokens import hash_token

PASSWORD_RESET = "password_reset"
ACCOUNT_RESTORE = "account_restore"

_MESSAGES = {
    PASSWORD_RESET: {
        "invalid": "Invalid password reset token",
        "used": "Password reset token has already been used",
        "expired": "Password reset token has expired",
    },
    ACCOUNT_RESTORE: {
        "invalid": "Invalid account restore token",
        "used": "Account restore token has already been used",
        "expired": "Account restore token has expired",
    },
}


def token_error_message(purpose: str, problem: str) -> str:
    return _MESSAGES[purpose][problem]


def create_password_reset_token(
    auth_repo: AuthenticationRepository,
    user_id: int,
    purpose: str = PASSWORD_RESET,
) -> str:
    token = secrets.token_urlsafe(32)

    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.reset_password_token_expire_minutes,
    )

    auth_repo.create_password_reset_token(
        user_id, hash_token(token), expires_at, purpose
    )
    return token


def verify_password_reset_token(
    auth_repo: AuthenticationRepository,
    token: str,
    purpose: str = PASSWORD_RESET,
):
    db_token = auth_repo.get_password_reset_token_by_hash(hash_token(token), purpose)

    if not db_token:
        raise InvalidResetTokenError(token_error_message(purpose, "invalid"))
    if db_token.used_at is not None:
        raise ResetTokenAlreadyUsedError(token_error_message(purpose, "used"))
    if db_token.expires_at <= datetime.now(UTC):
        raise BadRequestError(token_error_message(purpose, "expired"))
    return db_token
