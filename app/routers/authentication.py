from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models, schemas
from app.core.database import get_db
from app.dependencies import get_auth_repo, get_user_repo
from app.oauth2 import get_current_user
from app.repositories.authentication import AuthenticationRepository
from app.repositories.user import UserRepository
from app.services.authentication.login import login as login_service
from app.services.authentication.login import logout as logout_service
from app.services.authentication.login import logout_all as logout_all_service
from app.services.authentication.password import (
    change_password as change_password_service,
)
from app.services.authentication.password import (
    forgot_password as forgot_password_service,
)
from app.services.authentication.password import (
    reset_password as reset_password_service,
)
from app.services.authentication.password import (
    verify_token as verify_token_service,
)
from app.services.authentication.tokens import refresh_token as refresh_token_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/", response_model=schemas.Token)
def login(
    request: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
):
    return login_service(
        request=request, db=db, user_repo=user_repo, auth_repo=auth_repo
    )


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(
    request: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):

    return refresh_token_service(
        db=db,
        request=request,
        auth_repo=auth_repo,
        user_repo=user_repo,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: schemas.LogoutRequest,
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
    db: Session = Depends(get_db),
):

    return logout_service(request=request, db=db, auth_repo=auth_repo)


@router.post("/forgot-password")
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
):
    return forgot_password_service(
        request=request, db=db, user_repo=user_repo, auth_repo=auth_repo
    )


@router.post("/reset-password")
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    return reset_password_service(
        request=request, db=db, auth_repo=auth_repo, user_repo=user_repo
    )


@router.post("/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
):
    return change_password_service(
        db=db, request=request, current_user=current_user, auth_repo=auth_repo
    )


@router.post("/logout-all")
def logout_all_session(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
):
    return logout_all_service(db=db, current_user=current_user, auth_repo=auth_repo)


# takes the reset-password token and verifies it if it's valid or not
# validates token in the frontend before sending the user to the reset-password pagfe
# if the token is invalid, the user will be redirected to the forgot-password page or gives an error message


@router.post("/verify-token")
def verify_token(
    request: schemas.ResetPasswordToken,
    auth_repo: AuthenticationRepository = Depends(get_auth_repo),
):
    return verify_token_service(request=request, auth_repo=auth_repo)
