"""Rate limiting: the limiter itself, then what it does to the public endpoints.

The rest of the suite runs with limiting switched off (see rate_limiting_off in
conftest.py). Here a real limiter on in-memory storage is swapped in."""

import pytest

from app.core.exceptions import TooManyRequestsError
from app.core.rate_limit import RateLimiter
from app.core.security import Hash
from app.dependencies import get_rate_limiter
from app.main import app
from app.services.authentication import login as login_service
from app.services.authentication import password as password_service

PASSWORD = "TestPassword123!"
TOO_MANY = {"detail": "Too many attempts. Please try again later."}


@pytest.fixture
def limiter():
    real = RateLimiter("memory://")
    previous = app.dependency_overrides.get(get_rate_limiter)
    app.dependency_overrides[get_rate_limiter] = lambda: real
    yield real
    app.dependency_overrides[get_rate_limiter] = previous


def sign_in(client, username: str, password: str = PASSWORD):
    return client.post("/auth/", data={"username": username, "password": password})


# --- the limiter on its own --------------------------------------------------------


def test_check_counts_every_call_and_refuses_after_the_limit():
    limiter = RateLimiter("memory://")
    for _ in range(3):
        limiter.check("scope", "key", "3 per minute")

    with pytest.raises(TooManyRequestsError) as refused:
        limiter.check("scope", "key", "3 per minute")

    assert refused.value.status_code == 429
    assert 1 <= int(refused.value.headers["Retry-After"]) <= 60


def test_ensure_allowed_looks_without_counting():
    limiter = RateLimiter("memory://")
    for _ in range(10):
        limiter.ensure_allowed("scope", "key", "2 per minute")  # never refuses

    limiter.record("scope", "key", "2 per minute")
    limiter.record("scope", "key", "2 per minute")
    with pytest.raises(TooManyRequestsError):
        limiter.ensure_allowed("scope", "key", "2 per minute")


def test_clear_forgets_the_count():
    limiter = RateLimiter("memory://")
    limiter.record("scope", "key", "1 per minute")
    limiter.clear("scope", "key", "1 per minute")

    limiter.ensure_allowed("scope", "key", "1 per minute")


def test_keys_and_scopes_do_not_share_counts():
    limiter = RateLimiter("memory://")
    limiter.check("a", "key", "1 per minute")

    limiter.check("a", "other-key", "1 per minute")
    limiter.check("b", "key", "1 per minute")


# --- login: only failures count, per address and account ------------------------------


def test_login_is_locked_after_five_failures(client, limiter, make_user):
    user = make_user()
    for _ in range(5):
        assert sign_in(client, user.username, "wrong-password").status_code == 401

    blocked = sign_in(client, user.username, "wrong-password")

    assert blocked.status_code == 429
    assert blocked.json() == TOO_MANY
    assert int(blocked.headers["retry-after"]) > 0
    # while locked even the right password is refused, or guessing would just continue
    assert sign_in(client, user.username).status_code == 429


def test_accounts_that_do_not_exist_are_limited_in_the_same_way(client, limiter):
    for _ in range(5):
        assert sign_in(client, "ghost", "whatever123").status_code == 401

    assert sign_in(client, "ghost", "whatever123").status_code == 429


def test_a_correct_password_clears_the_failures(client, limiter, make_user):
    user = make_user()
    for _ in range(4):
        sign_in(client, user.username, "wrong-password")
    assert sign_in(client, user.username).status_code == 200

    for _ in range(4):
        assert sign_in(client, user.username, "wrong-password").status_code == 401


def test_one_locked_account_does_not_lock_the_others(client, limiter, make_user):
    locked, other = make_user(), make_user()
    for _ in range(6):
        sign_in(client, locked.username, "wrong-password")

    assert sign_in(client, locked.username).status_code == 429
    assert sign_in(client, other.username).status_code == 200


def test_the_login_lock_ignores_letter_case(client, limiter, make_user):
    user = make_user()
    for _ in range(5):
        sign_in(client, user.username.upper(), "wrong-password")

    assert sign_in(client, user.username.lower(), "wrong-password").status_code == 429


def test_an_unknown_account_still_pays_for_a_password_check(
    client, limiter, monkeypatch
):
    hashed_values = []
    monkeypatch.setattr(
        Hash, "verify_password", lambda plain, hashed: hashed_values.append(hashed)
    )

    sign_in(client, "ghost", "whatever123")

    # a missing user takes as long to refuse as a wrong password, so timing reveals nothing
    assert hashed_values == [login_service._DUMMY_HASH]


# --- per-address caps on the public endpoints --------------------------------------


def test_login_is_capped_per_address(client, limiter):
    for i in range(20):
        assert sign_in(client, f"nobody{i}", "whatever123").status_code == 401

    blocked = sign_in(client, "nobody-else", "whatever123")

    assert blocked.status_code == 429
    assert blocked.json() == TOO_MANY


def test_registration_is_capped_per_address(client, limiter, roles):
    def register(i: int):
        return client.post(
            "/users/",
            json={
                "username": f"person{i}",
                "email": f"person{i}@example.com",
                "password": "StrongPass123!",
            },
        )

    for i in range(5):
        assert register(i).status_code == 201

    assert register(5).status_code == 429


@pytest.mark.parametrize(
    ("path", "body", "limit"),
    [
        ("/auth/refresh", {"refresh_token": "x"}, 60),
        ("/auth/logout", {"refresh_token": "x"}, 60),
        ("/auth/verify-token", {"reset_token": "x"}, 30),
        (
            "/auth/reset-password",
            {"token": "x", "new_password": "NewPassword123!"},
            10,
        ),
    ],
)
def test_public_endpoints_are_capped_per_address(client, limiter, path, body, limit):
    for _ in range(limit):
        assert client.post(path, json=body).status_code != 429

    assert client.post(path, json=body).status_code == 429


# --- forgot-password: per email and per address --------------------------------------


@pytest.fixture
def sent_resets(monkeypatch):
    sent = []
    monkeypatch.setattr(
        password_service, "send_password_reset_email", lambda **kw: sent.append(kw)
    )
    return sent


def forgot(client, email: str):
    return client.post("/auth/forgot-password", json={"email": email})


def test_forgot_password_is_limited_per_email(client, limiter, make_user, sent_resets):
    user = make_user()
    for _ in range(3):
        assert forgot(client, user.email).status_code == 200

    blocked = forgot(client, user.email)

    assert blocked.status_code == 429
    assert len(sent_resets) == 3  # nobody's inbox gets flooded
    assert forgot(client, "someone.else@example.com").status_code == 200


def test_forgot_password_limits_unknown_emails_exactly_the_same(client, limiter):
    for _ in range(3):
        assert forgot(client, "nobody@example.com").status_code == 200

    # the limit never depends on whether the account exists, so it reveals nothing
    assert forgot(client, "nobody@example.com").status_code == 429


def test_forgot_password_is_capped_per_address(client, limiter):
    for i in range(10):
        assert forgot(client, f"person{i}@example.com").status_code == 200

    assert forgot(client, "one.more@example.com").status_code == 429
