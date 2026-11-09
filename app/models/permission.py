from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.role_permission import role_permissions


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(
        Integer,
        primary_key=True,
    )
    name = Column(String(100), unique=True, nullable=False)

    roles = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )
