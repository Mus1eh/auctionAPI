"""Restoring a soft-deleted account by emailed token.

The token lives in password_reset_tokens with purpose "account_restore", so it can
never be used as a password reset token, and the other way round."""

from datetime import UTC, datetime, timedelta

import pytest

from app import models
from app.core.rate_limit import RateLimiter
from app.dependencies import get_rate_limiter
from app.main import app
from app.services.authentication.refresh_tokens import hash_token
from app.services.authentication.reset_tokens import ACCOUNT_RESTORE, PASSWORD_RESET

PASSWORD = "TestPassword123!"
SENT = {"message": "If the email exists, an account restore link will be sent."}


@pytest.fixture
def deleted_user(db_session, make_user):
    user = make_user()
    user.deleted_at = datetime.now(UTC)
    db_session.flush()
    return user


def make_token(
    db_session,
    user,
    raw="restore-token",
    purpose=ACCOUNT_RESTORE,
    expires_in=timedelta(hours=1),
    used=False,
):
    db_session.add(
        models.PasswordResetToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=hash_token(raw),
            expires_at=datetime.now(UTC) + expires_in,
            used_at=datetime.now(UTC) if used else None,
        )
    )
    db_session.flush()
    return raw


def request_restore(client, email):
    return client.post("/users/restore-request", json={"email": email})


def confirm(client, token):
    return client.post("/users/restore", json={"token": token})


def outbox_for(db_session, email):
    return db_session.query(models.EmailOutbox).filter_by(to_email=email).all()


# --- asking for the link ---------------------------------------------------------


def test_request_queues_email_with_restore_token(client, db_session, deleted_user):
    response = request_restore(client, deleted_user.email)

    assert response.status_code == 202
    assert response.json() == SENT

    token = db_session.query(models.PasswordResetToken).one()
    assert token.user_id == deleted_user.id
    assert token.purpose == ACCOUNT_RESTORE

    mail = outbox_for(db_session, deleted_user.email)
    assert len(mail) == 1
    assert "/restore-account?token=" in mail[0].body
    assert mail[0].status == "pending"


def test_request_for_active_or_unknown_email_looks_the_same_and_sends_nothing(
    client, db_session, make_user
):
    active = make_user()

    for email in (active.email, "nobody@example.com"):
        response = request_restore(client, email)
        assert response.status_code == 202
        assert response.json() == SENT

    assert db_session.query(models.PasswordResetToken).count() == 0
    assert db_session.query(models.EmailOutbox).count() == 0


def test_request_is_limited_per_email(client, deleted_user):
    real = RateLimiter("memory://")
    app.dependency_overrides[get_rate_limiter] = lambda: real

    for _ in range(3):
        assert request_restore(client, deleted_user.email).status_code == 202

    refused = request_restore(client, deleted_user.email)
    assert refused.status_code == 429
    assert "Retry-After" in refused.headers


# --- using the token -------------------------------------------------------------


def test_confirm_restores_the_account_and_user_can_log_in(
    client, db_session, deleted_user
):
    username = deleted_user.username
    assert (
        client.post("/auth/", data={"username": username, "password": PASSWORD})
    ).status_code != 200

    raw = make_token(db_session, deleted_user)
    response = confirm(client, raw)

    assert response.status_code == 200
    db_session.expire_all()
    assert deleted_user.deleted_at is None
    assert db_session.query(models.PasswordResetToken).one().used_at is not None
    assert len(outbox_for(db_session, deleted_user.email)) == 1

    login = client.post("/auth/", data={"username": username, "password": PASSWORD})
    assert login.status_code == 200


def test_confirm_token_works_once(client, db_session, deleted_user):
    raw = make_token(db_session, deleted_user)

    assert confirm(client, raw).status_code == 200
    again = confirm(client, raw)

    assert again.status_code == 400
    assert again.json() == {"detail": "Account restore token has already been used"}


def test_confirm_rejects_expired_token(client, db_session, deleted_user):
    raw = make_token(db_session, deleted_user, expires_in=-timedelta(minutes=1))

    response = confirm(client, raw)

    assert response.status_code == 400
    assert response.json() == {"detail": "Account restore token has expired"}
    db_session.expire_all()
    assert deleted_user.deleted_at is not None


def test_confirm_rejects_unknown_token(client):
    response = confirm(client, "nope")

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid account restore token"}


def test_confirm_rejects_a_password_reset_token(client, db_session, deleted_user):
    raw = make_token(db_session, deleted_user, purpose=PASSWORD_RESET)

    assert confirm(client, raw).status_code == 400
    db_session.expire_all()
    assert deleted_user.deleted_at is not None


def test_confirm_for_an_active_account_changes_nothing(client, db_session, make_user):
    active = make_user()
    raw = make_token(db_session, active)

    assert confirm(client, raw).status_code == 400
    assert outbox_for(db_session, active.email) == []


# --- a restore token is useless for passwords ------------------------------------


def test_restore_token_cannot_reset_a_password_or_pass_verify(
    client, db_session, make_user
):
    user = make_user()
    raw = make_token(db_session, user)

    verify = client.post("/auth/verify-token", json={"reset_token": raw})
    reset = client.post(
        "/auth/reset-password", json={"token": raw, "new_password": "NewPassword123!"}
    )

    assert verify.status_code == 400
    assert reset.status_code == 400
