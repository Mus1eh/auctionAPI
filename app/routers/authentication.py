from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, update
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.email_service import send_password_reset_email
from app.hashing import Hash
from app.oauth2 import create_access_token, get_current_user
from app.password_reset import create_password_reset_token, verify_password_reset_token
from app.refresh_token import create_refresh_token, hash_token, verify_refresh_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/", response_model=schemas.Token)
def login(
    request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(
            or_(
                models.User.username == request.username,
                models.User.email == request.username,
            )
        )
        .first()
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


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(request: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    db_token = verify_refresh_token(db, request.refresh_token)

    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="user no longer exists",
        )

    result = db.execute(
        update(models.RefreshToken)
        .where(
            models.RefreshToken.id == db_token.id,
            models.RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
        .execution_options(synchronize_session="fetch")
    )

    if result.rowcount != 1:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to revoke the refresh token.",
        )
    try:
        new_refresh_token = create_refresh_token(db, user.id)

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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: schemas.LogoutRequest, db: Session = Depends(get_db)):
    db.execute(
        update(models.RefreshToken)
        .where(
            models.RefreshToken.token_hash == hash_token(request.refresh_token),
            models.RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
        .execution_options(synchronize_session="fetch")
    )
    db.commit()


@router.post("/forgot-password")
def forgot_password(
    request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if user:
        try:
            token = create_password_reset_token(db, user.id)
            db.commit()

        except Exception:
            db.rollback()
            raise

        send_password_reset_email(to_email=user.email, reset_token=token)

    return {"message": "If the email exists, a password reset link will be sent"}


@router.post("/reset-password")
def reset_password(
    request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    db_token = verify_password_reset_token(db, request.token)

    user = db.query(models.User).filter(models.User.id == db_token.user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset token",
        )

    # revoking the token

    try:
        result = db.execute(
            update(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.id == db_token.id,
                models.PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        if result.rowcount != 1:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has already been used",
            )

        # updating user's password and make sure that it's not the same as the old password

        if Hash.verify_password(request.new_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as the old password",
            )
        user.password = Hash.crypt_password(request.new_password)

        # revoking all existing reset tokens for the user --> terminating all the sessions for the user

        db.execute(
            update(models.RefreshToken)
            .where(
                models.RefreshToken.user_id == user.id,
                models.RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        # invalidating all the reset tokens for the user

        db.execute(
            update(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.user_id == user.id,
                models.PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {"message": "Password has been reset successfully"}


@router.post("/change-password")
def change_password(
    request: schemas.ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):

    # Verify current password
    if not Hash.verify_password(request.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Prevent using current password

    if Hash.verify_password(request.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password",
        )

    try:
        # update the user's password with the new password

        current_user.password = Hash.crypt_password(request.new_password)

        # Revoke all existing refresh tokens for the user to terminate all sessions

        db.execute(
            update(models.RefreshToken)
            .where(
                models.RefreshToken.user_id == current_user.id,
                models.RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        # Invalidate unused password reset tokens for the user

        db.execute(
            update(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.user_id == current_user.id,
                models.PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"message": "Password has been changed successfully"}


@router.post("/logout-all")
def logout_all_session(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    try:
        result = db.execute(
            update(models.RefreshToken)
            .where(
                models.RefreshToken.user_id == current_user.id,
                models.RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "All sessions have been logged out successfully",
        "count": result.rowcount,
    }


# takes the reset-password token and verifies it if it's valid or not
# validates token in the frontend before sending the user to the reset-password pagfe
# if the token is invalid, the user will be redirected to the forgot-password page or gives an error message
@router.post("/verify-token")
def verify_token(request: schemas.ResetPasswordToken, db: Session = Depends(get_db)):
    db_token = verify_password_reset_token(db, request.reset_token)
    return db_token
