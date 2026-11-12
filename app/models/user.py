from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.limits import EMAIL_MAX, USERNAME_MAX
from app.models.mixin import SoftDeleteMixin
from app.models.user_role import user_roles


class User(SoftDeleteMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(USERNAME_MAX), unique=True, nullable=False)
    email = Column(String(EMAIL_MAX), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    products = relationship(
        "Product", back_populates="owner", cascade="all, delete-orphan"
    )

    roles = relationship(
        "Role",
        secondary=user_roles,
        back_populates="users",
    )

    bids = relationship("Bids", back_populates="bidder", cascade="all, delete-orphan")
