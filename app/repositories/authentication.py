from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from app import models


class AuthenticationRepository:
    def __init__(self, db: Session):
        self.db = db

    def refresh_token_update(self, db_token: models.RefreshToken):
        result = self.db.execute(
            update(models.RefreshToken)
            .where(
                models.RefreshToken.id == db_token.id,
                models.RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        self.db.flush()
        return result.rowcount

    def password_reset_token_update(self, db_token: models.PasswordResetToken):
        result = self.db.execute(
            update(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.id == db_token.id,
                models.PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        self.db.flush()
        return result.rowcount

    def revoke_all_refresh_token_by_user_id(self, user_id: int):
        result = self.db.execute(
            update(models.RefreshToken)
            .where(
                models.RefreshToken.user_id == user_id,
                models.RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        self.db.flush()
        return result.rowcount

    def revoke_all_password_reset_token_by_user_id(self, user_id: int):
        self.db.execute(
            update(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.user_id == user_id,
                models.PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )
        self.db.flush()

    def logout(self, token_hash: str):
        self.db.execute(
            update(models.RefreshToken)
            .where(
                models.RefreshToken.token_hash == token_hash,
                models.RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
            .execution_options(synchronize_session="fetch")
        )

        self.db.flush()

    def create_refresh_token(self, user_id: int, token_hash: str, expires_at: datetime):
        db_token = models.RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        self.db.flush()
        return db_token

    def get_refresh_token_by_hash(self, token_hash: str):
        return (
            self.db.query(models.RefreshToken)
            .filter(
                models.RefreshToken.token_hash == token_hash,
            )
            .first()
        )

    def create_password_reset_token(
        self, user_id: int, token_hash: str, expires_at: datetime
    ):
        db_token = models.PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(db_token)
        self.db.flush()
        return db_token

    def get_password_reset_token_by_hash(self, token_hash: str):
        return (
            self.db.query(models.PasswordResetToken)
            .filter(
                models.PasswordResetToken.token_hash == token_hash,
            )
            .first()
        )
