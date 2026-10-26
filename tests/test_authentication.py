from app import models
from app.hashing import Hash


def test_login_with_username_and_email(client, make_user):
    user = make_user()
    for identifier in (user.username, user.email):
        response = client.post(
            "/auth/", data={"username": identifier, "password": "TestPassword123!"}
        )
        assert response.status_code == 200, response.text
        assert response.json()["access_token"]
        assert response.json()["refresh_token"]


def test_invalid_credentials(client, make_user):
    user = make_user()
    for username, password in [("missing", "wrong"), (user.username, "wrong")]:
        assert (
            client.post(
                "/auth/", data={"username": username, "password": password}
            ).status_code
            == 401
        )


def test_refresh_rotation_and_reuse(client, make_user):
    user = make_user()
    original = client.post(
        "/auth/", data={"username": user.username, "password": "TestPassword123!"}
    ).json()["refresh_token"]
    refreshed = client.post("/auth/refresh", json={"refresh_token": original})
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["refresh_token"] != original
    assert (
        client.post("/auth/refresh", json={"refresh_token": original}).status_code
        == 401
    )


def test_logout_revokes_refresh_token(client, make_user):
    user = make_user()
    token = client.post(
        "/auth/", data={"username": user.username, "password": "TestPassword123!"}
    ).json()["refresh_token"]
    assert client.post("/auth/logout", json={"refresh_token": token}).status_code == 204
    assert (
        client.post("/auth/refresh", json={"refresh_token": token}).status_code == 401
    )


def test_logout_all(client, make_user, auth):
    user = make_user()
    token = client.post(
        "/auth/", data={"username": user.username, "password": "TestPassword123!"}
    ).json()["refresh_token"]
    response = client.post("/auth/logout-all", headers=auth(user))
    assert response.status_code == 200, response.text
    assert response.json()["count"] >= 1
    assert (
        client.post("/auth/refresh", json={"refresh_token": token}).status_code == 401
    )


def test_change_password(client, db_session, make_user, auth):
    user = make_user()
    user_id = user.id
    username = user.username

    response = client.post(
        "/auth/change-password",
        headers=auth(user),
        json={
            "current_password": "TestPassword123!",
            "new_password": "ChangedPassword123!",
        },
    )

    # 1. Password change request must succeed
    assert response.status_code == 200, response.text

    # 2. Refresh cached SQLAlchemy objects
    db_session.expire_all()

    # 3. Reload the user from the database
    updated_user = db_session.get(models.User, user_id)

    assert updated_user is not None

    # 4. Verify the new password hash
    assert Hash.verify_password(
        "ChangedPassword123!",
        updated_user.password,
    )

    # 5. Old password must no longer work
    old_login = client.post(
        "/auth/",
        data={
            "username": username,
            "password": "TestPassword123!",
        },
    )

    assert old_login.status_code == 401, old_login.text

    # 6. New password must work
    new_login = client.post(
        "/auth/",
        data={
            "username": username,
            "password": "ChangedPassword123!",
        },
    )

    assert new_login.status_code == 200, new_login.text


def test_change_password_wrong_old(client, make_user, auth):
    user = make_user()
    response = client.post(
        "/auth/change-password",
        headers=auth(user),
        json={"current_password": "wrong", "new_password": "ChangedPassword123!"},
    )
    assert response.status_code == 400


def test_forgot_password_unknown_email(client):
    response = client.post(
        "/auth/forgot-password", json={"email": "missing@example.com"}
    )
    assert response.status_code == 200, response.text


def test_forgot_and_reset_password(client, db_session, make_user, monkeypatch):
    import app.routers.authentication as auth_router

    sent = []
    monkeypatch.setattr(
        auth_router, "send_password_reset_email", lambda **kwargs: sent.append(kwargs)
    )
    user = make_user()
    response = client.post("/auth/forgot-password", json={"email": user.email})
    assert response.status_code == 200, response.text
    assert len(sent) == 1
    token = sent[0]["reset_token"]
    assert (
        client.post("/auth/verify-token", json={"reset_token": token}).status_code
        == 200
    )
    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "AnotherPassword123!"},
    )
    assert response.status_code == 200, response.text
    assert client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "YetAnotherPassword123!"},
    ).status_code in (400, 401)
    assert (
        client.post(
            "/auth/",
            data={"username": user.username, "password": "AnotherPassword123!"},
        ).status_code
        == 200
    )


def test_invalid_reset_token(client):
    assert client.post(
        "/auth/reset-password",
        json={"token": "invalid", "new_password": "NewPassword123!"},
    ).status_code in (400, 401)
    assert client.post(
        "/auth/verify-token", json={"reset_token": "invalid"}
    ).status_code in (400, 401)
