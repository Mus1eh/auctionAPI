from sqlalchemy.orm import Session

from app import schemas
from app.core.config import settings
from app.core.exceptions import InvalidResetTokenError, ResetTokenAlreadyUsedError
from app.core.rate_limit import RateLimiter
from app.mailer.service import generate_user_restore_link
from app.mailer.templates import account_restore_request_email, restore_user_email
from app.repositories.authentication import AuthenticationRepository
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.user import UserRepository
from app.services.authentication.reset_tokens import (
    ACCOUNT_RESTORE,
    create_password_reset_token,
    verify_password_reset_token,
)

# Counted per submitted email whether or not the account exists, so the limit
# itself reveals nothing, and nobody's inbox can be flooded.
RESTORE_REQUEST_RULE = "3 per hour"


def request_user_restore(
    db: Session,
    request: schemas.UserRestore,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
    outbox_repo: EmailOutboxRepository,
    limiter: RateLimiter,
):
    limiter.check("restore-email", request.email.lower(), RESTORE_REQUEST_RULE)

    user = user_repo.get_by_email_for_restore(request.email)
    if user:
        try:
            token = create_password_reset_token(
                auth_repo, int(user.id), ACCOUNT_RESTORE
            )
            # Queued in the outbox, so the response does not wait on SMTP.
            outbox_repo.create(
                to_email=user.email,
                subject="Account Restore Request",
                body=account_restore_request_email(
                    user,
                    generate_user_restore_link(token),
                    settings.reset_password_token_expire_minutes,
                ),
            )
            db.commit()

        except Exception:
            db.rollback()
            raise

    return {"message": "If the email exists, an account restore link will be sent."}


def restore_user(
    db: Session,
    request: schemas.UserRestoreConfirm,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
    outbox_repo: EmailOutboxRepository,
):
    db_token = verify_password_reset_token(auth_repo, request.token, ACCOUNT_RESTORE)

    # Locked, so two requests with the same token cannot both restore.
    user = user_repo.get_by_id_for_restore(db_token.user_id)
    if not user:
        raise InvalidResetTokenError()

    try:
        if auth_repo.password_reset_token_update(db_token) != 1:
            raise ResetTokenAlreadyUsedError()

        user_repo.restore(user)
        auth_repo.revoke_all_password_reset_token_by_user_id(int(user.id))

        outbox_repo.create(
            to_email=user.email,
            subject="Your account has been restored",
            body=restore_user_email(user),
        )
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Your account has been restored. You can log in now."}
