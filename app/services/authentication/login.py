from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.exceptions import InvalidCredentialsError
from app.core.security import Hash, create_access_token
from app.repositories.authentication import AuthenticationRepository
from app.repositories.user import UserRepository
from app.services.authentication.refresh_tokens import create_refresh_token, hash_token


def login(
    request: OAuth2PasswordRequestForm,
    db: Session,
    user_repo: UserRepository,
    auth_repo: AuthenticationRepository,
):
    # The form's username field holds either an email or a username.
    user = user_repo.get_by_email(request.username) or user_repo.get_by_username(
        request.username
    )

    credential_exception = InvalidCredentialsError()
    if not user:
        raise credential_exception
    if not Hash.verify_password(request.password, user.password):
        raise credential_exception
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
