import uuid

from app import models


def test_register_user(client, roles, db_session):
    suffix = uuid.uuid4().hex[:10]

    payload = {
        "username": f"new_{suffix}",
        "email": f"{suffix}@example.com",
        "password": "StrongPassword123!",
    }

    response = client.post("/users/", json=payload)

    # New resource created
    assert response.status_code == 201, response.text

    # Validate the API response
    data = response.json()

    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert "password" not in data

    # Validate the database record
    saved = db_session.query(models.User).filter_by(username=payload["username"]).one()

    assert saved.role_name == "user"
    assert saved.password != payload["password"]


def test_duplicate_registration(client, make_user):
    user = make_user()
    response = client.post(
        "/users/",
        json={
            "username": user.username,
            "email": user.email,
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 400


def test_registration_validation(client):
    assert (
        client.post(
            "/users/", json={"username": "ab", "email": "bad", "password": "short"}
        ).status_code
        == 422
    )


def test_get_user_requires_admin(client, make_user, auth):
    user, other = make_user(), make_user()
    assert client.get(f"/users/{other.id}", headers=auth(user)).status_code == 403
    admin = make_user("admin")
    response = client.get(f"/users/{other.id}", headers=auth(admin))
    assert response.status_code == 200
    assert response.json()["id"] == other.id


def test_get_missing_user(client, make_user, auth):
    assert (
        client.get("/users/999999", headers=auth(make_user("admin"))).status_code == 404
    )


def test_user_can_delete_self(client, db_session, make_user, auth):
    user = make_user()
    user_id = user.id
    response = client.delete(f"/users/{user.id}", headers=auth(user))
    assert response.status_code == 202, response.text
    db_session.expire_all()
    assert db_session.get(models.User, user_id) is None


def test_user_cannot_delete_another_user(client, make_user, auth):
    user, other = make_user(), make_user()
    assert client.delete(f"/users/{other.id}", headers=auth(user)).status_code == 403


def test_cannot_delete_admin(client, make_user, auth):
    admin, superadmin = make_user("admin"), make_user("superadmin")
    assert (
        client.delete(f"/users/{admin.id}", headers=auth(superadmin)).status_code == 403
    )
