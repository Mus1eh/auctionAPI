from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.hashing import Hash
from app.oauth2 import create_access_token
from app.refresh_token import create_refresh_token
from app.repositories.authentication import AuthenticationRepository


def login(
    request: OAuth2PasswordRequestForm,
    db: Session,
    auth_repo: AuthenticationRepository,
):
    user = (
        auth_repo.get_user_by_email(request.username)
        if "@" in request.username
        else auth_repo.get_user_by_username(request.username)
    )

    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user:
        raise credential_exception
    if not Hash.verify_password(request.password, user.password):
        raise credential_exception
    access_token = create_access_token(data={"sub": user.username})
    try:
        refresh_token = create_refresh_token(db, user.id)
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
        auth_repo.logout(request)

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
