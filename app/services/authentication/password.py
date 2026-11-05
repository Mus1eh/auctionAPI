from sqlalchemy.orm import Session

from app import models, schemas
from app.core.exceptions import (
    BadRequestError,
    InvalidResetTokenError,
    ResetTokenAlreadyUsedError,
)
from app.core.security import Hash
from app.mailer.service import send_password_reset_email
from app.repositories.authentication import AuthenticationRepository
from app.repositories.user import UserRepository
from app.services.authentication.reset_tokens import (
    create_password_reset_token,
    verify_password_reset_token,
)


def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
):
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

    # revoking the token

    try:
        affected_rows = auth_repo.password_reset_token_update(db_token)

        if affected_rows != 1:
            db.rollback()
            raise ResetTokenAlreadyUsedError()

        # updating user's password and make sure that it's not the same as the old password

        if Hash.verify_password(request.new_password, user.password):
            raise BadRequestError("New password cannot be the same as the old password")
        user.password = Hash.crypt_password(request.new_password)

        # revoking all existing reset tokens for the user --> terminating all the sessions for the user

        auth_repo.revoke_all_refresh_token_by_user_id(int(user.id))

        # invalidating all the reset tokens for the user

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

    # Verify current password
    if not Hash.verify_password(request.current_password, current_user.password):
        raise BadRequestError("Current password is incorrect")

    # Prevent using current password

    if Hash.verify_password(request.new_password, current_user.password):
        raise BadRequestError("New password cannot be the same as the current password")

    try:
        # update the user's password with the new password

        current_user.password = Hash.crypt_password(request.new_password)

        # Revoke all existing refresh tokens for the user to terminate all sessions

        auth_repo.revoke_all_refresh_token_by_user_id(int(current_user.id))

        # Invalidate unused password reset tokens for the user

        auth_repo.revoke_all_password_reset_token_by_user_id(int(current_user.id))

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Password has been changed successfully"}


def verify_token(
    request: schemas.ResetPasswordToken, auth_repo: AuthenticationRepository
):
    # Raises the same errors as reset_password when the token is unknown, used or expired.
    verify_password_reset_token(auth_repo, request.reset_token)

    return {"message": "Password reset token is valid"}
