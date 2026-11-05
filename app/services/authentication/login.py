from sqlalchemy.orm import Session

from app import models, schemas
from app.core.exceptions import InvalidCredentialsError
from app.core.rate_limit import RateLimiter
from app.core.security import Hash, create_access_token
from app.repositories.authentication import AuthenticationRepository
from app.repositories.user import UserRepository
from app.services.authentication.refresh_tokens import create_refresh_token, hash_token

# Only failed attempts count, and a correct password clears them.
LOGIN_FAILURES_RULE = "5 per 15 minutes"

# Checked when the account does not exist, so refusing an unknown user takes as long as
# refusing a wrong password. Otherwise the response time shows which accounts exist.
_DUMMY_HASH = Hash.crypt_password("not-a-real-password")


def login(
    username: str,
    password: str,
    ip: str,
    db: Session,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
    limiter: RateLimiter,
):
    # Counted per address and account together, so a stranger cannot lock someone
    # out of their own account from somewhere else.
    attempts_key = f"{ip}|{username.strip().lower()}"
    limiter.ensure_allowed("login-failures", attempts_key, LOGIN_FAILURES_RULE)

    # The form's username field holds either an email or a username.
    user = user_repo.get_by_email(username) or user_repo.get_by_username(username)

    credential_exception = InvalidCredentialsError()
    if not user:
        Hash.verify_password(password, _DUMMY_HASH)
        limiter.record("login-failures", attempts_key, LOGIN_FAILURES_RULE)
        raise credential_exception
    if not Hash.verify_password(password, user.password):
        limiter.record("login-failures", attempts_key, LOGIN_FAILURES_RULE)
        raise credential_exception

    # A successful login clears failed attempts counter.
    limiter.clear("login-failures", attempts_key, LOGIN_FAILURES_RULE)
    access_token = create_access_token(data={"sub": user.username})
    try:
        refresh_token = create_refresh_token(auth_repo, user.id)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def logout(
    request: schemas.LogoutRequest, db: Session, auth_repo: AuthenticationRepository
):
    try:
        auth_repo.logout(hash_token(request.refresh_token))

        db.commit()

    except Exception:
        db.rollback()
        raise


def logout_all(
    db: Session,
    current_user: models.User,
    auth_repo: AuthenticationRepository,
):
    try:
        count = auth_repo.revoke_all_refresh_token_by_user_id(int(current_user.id))

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "All sessions have been logged out successfully",
        "count": count,
    }
