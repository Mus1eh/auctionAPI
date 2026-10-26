from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import ApprovalStatus, ProductStatus


class User(Base):
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


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    start_price = Column(Integer, nullable=False)
    current_price = Column(
        Integer,
        nullable=False,
    )

    owner_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner = relationship("User", back_populates="products")
    status = Column(
        SQLEnum(
            ProductStatus,
            name="product_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=ProductStatus.DRAFT,
    )
    status_requests = relationship(
        "ProductStatusRequest", back_populates="product", cascade="all, delete-orphan"
    )
    bids = relationship(
        "Bids",
        back_populates="product",
        foreign_keys="Bids.product_id",
        cascade="all, delete-orphan",
    )
    auction_started_at = Column(DateTime(timezone=True), nullable=True)
    auction_ends_at = Column(DateTime(timezone=True), nullable=True)

    winning_bid_id = Column(
        Integer, ForeignKey("bids.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    winning_bid = relationship("Bids", foreign_keys=[winning_bid_id], uselist=False)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="role")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash = Column(String(64), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)


class ProductStatusRequest(Base):
    __tablename__ = "product_status_requests"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_status = Column(
        SQLEnum(
            ProductStatus,
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
    )

    approval_status = Column(
        SQLEnum(
            ApprovalStatus,
            name="approval_status",
            values_callable=lambda enum_class: [item.value for item in enum_class],
        ),
        nullable=False,
        default=ApprovalStatus.PENDING,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    product = relationship("Product", back_populates="status_requests")


class Bids(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product = relationship("Product", back_populates="bids", foreign_keys=[product_id])
    bidder = relationship("User", back_populates="bids")


class EmailOutbox(Base):
    __tablename__ = "email_outbox"

    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(100), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)

    status = Column(String(20), nullable=False, default="pending")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sent_at = Column(DateTime(timezone=True), nullable=True)
