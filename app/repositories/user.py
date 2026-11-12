from datetime import UTC, datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def _query(self, include_deleted: bool = False):
        query = self.db.query(models.User)

        if not include_deleted:
            query = query.filter(models.User.deleted_at.is_(None))

        return query

    def get_by_id(self, user_id: int):
        return self._query().filter(models.User.id == user_id).first()

    def get_by_username(self, username: str):
        return self._query().filter(models.User.username == username).first()

    def get_by_email(self, email: str):
        return self._query().filter(models.User.email == email).first()

    def create(self, user: models.User):
        self.db.add(user)
        self.db.flush()
        return user

    def get_role_by_name(self, role_name: str):
        return self.db.query(models.Role).filter(models.Role.name == role_name).first()

    def has_role(self, user: models.User, role_name: str) -> bool:
        return any(role.name == role_name for role in user.roles)

    def assign_role(self, user: models.User, role: models.Role):
        if not self.has_role(user, role.name):
            user.roles.append(role)
        self.db.flush()
        return user

    def remove_role(self, user: models.User, role: models.Role):
        if self.has_role(user, role.name):
            user.roles.remove(role)
        self.db.flush()
        return user

    def softdelete(self, user: models.User):
        user.deleted_at = datetime.now(UTC)
        self.db.flush()
        return user

    # Soft-deleted users are included: their email and username still hold the unique constraints.
    def check_user_exists(self, username: str, email: str):
        return (
            self._query(include_deleted=True)
            .filter(
                or_(
                    models.User.email == email,
                    models.User.username == username,
                )
            )
            .first()
        )

    def get_by_id_for_update(self, user_id: int):
        return self._query().filter(models.User.id == user_id).with_for_update().first()
