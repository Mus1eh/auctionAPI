from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.mixin import SoftDeleteMixin


class User(SoftDeleteMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    products = relationship(
        "Product", back_populates="owner", cascade="all, delete-orphan"
    )

    role = relationship("Role", back_populates="users")
    role_name = Column(String(50), ForeignKey("roles.name"))
    bids = relationship("Bids", back_populates="bidder", cascade="all, delete-orphan")
