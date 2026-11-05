from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.core.database import Base


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
