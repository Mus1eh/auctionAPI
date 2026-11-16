from datetime import UTC, datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models

MAX_EMAIL_ATTEMPTS = 5
RETRY_BASE_SECONDS = 60


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
            .filter(
                or_(
                    models.EmailOutbox.next_attempt_at.is_(None),
                    models.EmailOutbox.next_attempt_at <= datetime.now(UTC),
                )
            )
            .order_by(models.EmailOutbox.id)
            .with_for_update(skip_locked=True)
            .first()
        )

    def mark_sent(self, email: models.EmailOutbox):
        email.status = "sent"
        email.sent_at = datetime.now(UTC)
        self.db.flush()
        return email

    def mark_failed(self, email: models.EmailOutbox, error: str):
        email.attempts += 1
        email.last_error = error[:1000]

        if email.attempts >= MAX_EMAIL_ATTEMPTS:
            email.status = "failed"
            email.next_attempt_at = None
        else:
            delay = RETRY_BASE_SECONDS * 2 ** (email.attempts - 1)
            email.next_attempt_at = datetime.now(UTC) + timedelta(seconds=delay)

        self.db.flush()
        return email
