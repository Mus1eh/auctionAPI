from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import schemas
from app.oauth2 import create_access_token
from app.refresh_token import create_refresh_token, verify_refresh_token
from app.repositories.authentication import AuthenticationRepository
from app.repositories.user import UserRepository


def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: Session,
    auth_repo: AuthenticationRepository,
    user_repo: UserRepository,
):

    db_token = verify_refresh_token(auth_repo, request.refresh_token)

    user = user_repo.get_by_id(db_token.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user no longer exists",
        )

    affected_rows = auth_repo.refresh_token_update(db_token)

    if affected_rows != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to revoke the refresh token.",
        )
    try:
        new_refresh_token = create_refresh_token(auth_repo, user.id)

        new_access_token = create_access_token(data={"sub": user.username})

        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
