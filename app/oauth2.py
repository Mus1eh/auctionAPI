from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/", auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )

    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        username = payload.get("sub")

        if not isinstance(username, str) or not username:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = UserRepository(db).get_by_username(username)

    if user is None:
        raise credentials_exception
    return user


def get_current_user_optional(
    token: str | None = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)
):
    if token is None:
        return None
    return get_current_user(token, db)
