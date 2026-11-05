"""The Celery tasks open their own sessions, so these tests point them at the
test connection. Everything is rolled back with the test's transaction."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app import models
from app.enums import ProductStatus
from app.worker import tasks


@pytest.fixture
def task_sessions(db_session, monkeypatch):
    connection = db_session.connection()

    def factory():
        return Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            autoflush=False,
        )

    monkeypatch.setattr(tasks, "sessionLocal", factory)


@pytest.fixture
def sent_emails(monkeypatch):
    sent = []
    monkeypatch.setattr(tasks, "send_auction_email", lambda **kw: sent.append(kw))
    return sent


def queue_email(db_session, subject: str):
    email = models.EmailOutbox(
        to_email="someone@example.com", subject=subject, body="body", status="pending"
    )
    db_session.add(email)
    db_session.flush()
    return email


def outbox_for(db_session, product_id: int):
    db_session.expire_all()
    return (
        db_session.query(models.EmailOutbox)
        .filter(models.EmailOutbox.subject.like(f"%Product #{product_id}"))
        .order_by(models.EmailOutbox.id)
        .all()
    )


# --- process_email_outbox ---------------------------------------------------


def test_outbox_sends_every_pending_email(db_session, task_sessions, sent_emails):
    emails = [queue_email(db_session, f"Mail {i}") for i in range(3)]

    result = tasks.process_email_outbox()

    assert result == {"sent": 3, "failed": 0}
    assert [mail["subject"] for mail in sent_emails] == ["Mail 0", "Mail 1", "Mail 2"]
    db_session.expire_all()
    for email in emails:
        assert email.status == "sent"
        assert email.sent_at is not None


def test_outbox_with_nothing_pending(db_session, task_sessions, sent_emails):
    assert tasks.process_email_outbox() == {"sent": 0, "failed": 0}
    assert sent_emails == []


def test_failed_email_is_marked_failed_and_not_retried(
    db_session, task_sessions, monkeypatch
):
    emails = [queue_email(db_session, f"Mail {i}") for i in range(3)]
    attempts = []

    def flaky_send(**kwargs):
        attempts.append(kwargs["subject"])
        if kwargs["subject"] == "Mail 1":
            raise RuntimeError("smtp down")

    monkeypatch.setattr(tasks, "send_auction_email", flaky_send)

    result = tasks.process_email_outbox()

    assert result == {"sent": 2, "failed": 1}
    # THE BROKEN EMAIL IS TRIED ONCE, NOT AGAIN ON EVERY PASS OF THE LOOP
    assert attempts == ["Mail 0", "Mail 1", "Mail 2"]
    db_session.expire_all()
    assert [email.status for email in emails] == ["sent", "failed", "sent"]
    assert emails[1].sent_at is None


def test_outbox_sends_at_most_twenty_emails_per_run(
    db_session, task_sessions, sent_emails
):
    for i in range(25):
        queue_email(db_session, f"Mail {i}")

    assert tasks.process_email_outbox() == {"sent": 20, "failed": 0}
    db_session.expire_all()
    pending = db_session.query(models.EmailOutbox).filter_by(status="pending").count()
    assert pending == 5


# --- close_expired_auctions -------------------------------------------------


def test_expired_auction_is_closed_and_both_parties_are_emailed(
    db_session, task_sessions, make_user, make_product, make_bid
):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.ACTIVE, ended=True)
    make_bid(product, bidder, 600)

    result = tasks.close_expired_auctions()

    assert result == {"Closed Auctions": 1}
    db_session.expire_all()
    assert product.status == ProductStatus.CLOSED
    emails = outbox_for(db_session, product.id)
    assert [(e.to_email, e.subject) for e in emails] == [
        (owner.email, f"Auction Closed - Product #{product.id}"),
        (bidder.email, f"Highest Bid - Product #{product.id}"),
    ]
    assert all(e.status == "pending" for e in emails)


def test_expired_auction_without_bids_only_emails_the_owner(
    db_session, task_sessions, make_user, make_product
):
    owner = make_user()
    product = make_product(owner, ProductStatus.ACTIVE, ended=True)

    assert tasks.close_expired_auctions() == {"Closed Auctions": 1}

    emails = outbox_for(db_session, product.id)
    assert [e.to_email for e in emails] == [owner.email]


def test_running_auction_is_left_alone(
    db_session, task_sessions, make_user, make_product
):
    product = make_product(make_user(), ProductStatus.ACTIVE)

    assert tasks.close_expired_auctions() == {"Closed Auctions": 0}

    db_session.expire_all()
    assert product.status == ProductStatus.ACTIVE
    assert outbox_for(db_session, product.id) == []


def test_deleted_expired_auction_is_not_closed(
    db_session, task_sessions, make_user, make_product
):
    product = make_product(make_user(), ProductStatus.ACTIVE, ended=True)
    product.deleted_at = datetime.now(UTC) - timedelta(minutes=1)
    db_session.flush()

    assert tasks.close_expired_auctions() == {"Closed Auctions": 0}

    db_session.expire_all()
    assert product.status == ProductStatus.ACTIVE
    assert outbox_for(db_session, product.id) == []
