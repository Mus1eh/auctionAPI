from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.enums import ApprovalStatus, ProductStatus


class ProductStatusRequest(Base):
    __tablename__ = "product_status_requests"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    requested_by = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
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
    # SET NULL -> IF THE REVIEWING ADMIN IS DELETED THE REQUEST (AND ITS HISTORY) STAYS
    reviewed_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    product = relationship("Product", back_populates="status_requests")
