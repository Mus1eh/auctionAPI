from sqlalchemy.orm import Session

from app import models, schemas
from app.core.exceptions import (
    BadRequestError,
    InvalidResetTokenError,
    ResetTokenAlreadyUsedError,
)
from app.core.rate_limit import RateLimiter
from app.core.security import Hash
from app.mailer.service import send_password_reset_email
from app.repositories.authentication import AuthenticationRepository
from app.repositories.user import UserRepository
from app.services.authentication.reset_tokens import (
    create_password_reset_token,
    verify_password_reset_token,
)

# Counted per submitted email whether or not the account exists, so the limit
# itself reveals nothing, and nobody's inbox can be flooded.
FORGOT_PASSWORD_RULE = "3 per hour"


def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
    limiter: RateLimiter,
):
    limiter.check("forgot-password-email", request.email.lower(), FORGOT_PASSWORD_RULE)

    user = user_repo.get_by_email(request.email)
    if user:
        try:
            token = create_password_reset_token(auth_repo, user.id)
            db.commit()

        except Exception:
            db.rollback()
            raise

        send_password_reset_email(to_email=user.email, reset_token=token)

    return {"message": "If the email exists, a password reset link will be sent"}


def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session,
    auth_repo: AuthenticationRepository,
    user_repo: UserRepository,
):
    db_token = verify_password_reset_token(auth_repo, request.token)

    user = user_repo.get_by_id(db_token.user_id)

    if not user:
        raise InvalidResetTokenError()

    try:
        affected_rows = auth_repo.password_reset_token_update(db_token)

        if affected_rows != 1:
            db.rollback()
            raise ResetTokenAlreadyUsedError()

        if Hash.verify_password(request.new_password, user.password):
            raise BadRequestError("New password cannot be the same as the old password")
        user.password = Hash.crypt_password(request.new_password)

        auth_repo.revoke_all_refresh_token_by_user_id(int(user.id))

        auth_repo.revoke_all_password_reset_token_by_user_id(int(user.id))

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Password has been reset successfully"}


def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session,
    current_user: models.User,
    auth_repo: AuthenticationRepository,
):

    if not Hash.verify_password(request.current_password, current_user.password):
        raise BadRequestError("Current password is incorrect")

    if Hash.verify_password(request.new_password, current_user.password):
        raise BadRequestError("New password cannot be the same as the current password")

    try:
        current_user.password = Hash.crypt_password(request.new_password)

        auth_repo.revoke_all_refresh_token_by_user_id(int(current_user.id))

        auth_repo.revoke_all_password_reset_token_by_user_id(int(current_user.id))

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Password has been changed successfully"}


def verify_token(
    request: schemas.ResetPasswordToken, auth_repo: AuthenticationRepository
):
    verify_password_reset_token(auth_repo, request.reset_token)

    return {"message": "Password reset token is valid"}
