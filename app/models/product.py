from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums import ProductStatus
from app.mixin import SoftDeleteMixin


class Product(SoftDeleteMixin, Base):
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
    # post_update BREAKS THE products <-> bids FK CYCLE: winning_bid_id IS SET/CLEARED IN A
    # SEPARATE UPDATE, SO DELETING A PRODUCT TOGETHER WITH ITS BIDS (E.G. DELETING ITS OWNER) WORKS
    winning_bid = relationship(
        "Bids", foreign_keys=[winning_bid_id], uselist=False, post_update=True
    )
