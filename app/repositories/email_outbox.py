from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models


class EmailOutboxRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, to_email: str, subject: str, body: str):
        email = models.EmailOutbox(
            to_email=to_email,
            subject=subject,
            body=body,
            status="pending",
        )

        self.db.add(email)
        self.db.flush()
        return email

    def get_next_pending_for_update(self):
        return (
            self.db.query(models.EmailOutbox)
            .filter(models.EmailOutbox.status == "pending")
            .order_by(models.EmailOutbox.id)
            .with_for_update(skip_locked=True)
            .first()
        )

    def mark_sent(self, email: models.EmailOutbox):
        email.status = "sent"
        email.sent_at = datetime.now(UTC)
        self.db.flush()
        return email

    def mark_failed(self, email: models.EmailOutbox):
        email.status = "failed"
        self.db.flush()
        return email
