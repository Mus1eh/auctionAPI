import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app import models
from app.enums import ApprovalStatus, ProductStatus


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
    assert response.status_code == 409


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
    assert db_session.get(models.User, user_id).deleted_at is not None


def test_user_cannot_delete_another_user(client, make_user, auth):
    user, other = make_user(), make_user()
    assert client.delete(f"/users/{other.id}", headers=auth(user)).status_code == 403


def test_admin_cannot_delete_another_admin(client, make_user, auth):
    admin, other_admin = make_user("admin"), make_user("admin")
    assert (
        client.delete(f"/users/{other_admin.id}", headers=auth(admin)).status_code
        == 403
    )


def test_admin_can_delete_self(client, make_user, auth):
    admin = make_user("admin")
    assert client.delete(f"/users/{admin.id}", headers=auth(admin)).status_code == 202


def test_admin_can_delete_user(client, make_user, auth):
    admin, user = make_user("admin"), make_user()
    assert client.delete(f"/users/{user.id}", headers=auth(admin)).status_code == 202


def test_superadmin_can_delete_admin(client, make_user, auth):
    admin, superadmin = make_user("admin"), make_user("superadmin")
    assert (
        client.delete(f"/users/{admin.id}", headers=auth(superadmin)).status_code == 202
    )


def test_cannot_delete_superadmin(client, make_user, auth):
    superadmin = make_user("superadmin")
    assert (
        client.delete(f"/users/{superadmin.id}", headers=auth(superadmin)).status_code
        == 403
    )


def test_delete_my_account(client, db_session, make_user, auth):
    user = make_user()
    user_id = user.id
    response = client.delete("/users/me", headers=auth(user))
    assert response.status_code == 202, response.text
    db_session.expire_all()
    assert db_session.get(models.User, user_id).deleted_at is not None


def test_delete_my_account_requires_login(client):
    assert client.delete("/users/me").status_code == 401


def test_superadmin_cannot_delete_own_account(client, make_user, auth):
    assert (
        client.delete("/users/me", headers=auth(make_user("superadmin"))).status_code
        == 403
    )


def test_delete_account_with_sold_products_and_bids(
    client, db_session, make_user, make_product, make_bid, auth
):
    # SOFT DELETE KEEPS THE SOLD PRODUCT AND ITS WINNING BID FOR HISTORY
    seller, bidder = make_user(), make_user()
    seller_id, bidder_id = seller.id, bidder.id
    product = make_product(seller, ProductStatus.SOLD, ended=True)
    winning_bid_id = make_bid(product, bidder, 600).id
    product.winning_bid_id = winning_bid_id
    make_bid(product, bidder, 550)
    db_session.flush()
    product_id = product.id

    response = client.delete("/users/me", headers=auth(seller))
    assert response.status_code == 202, response.text
    db_session.expire_all()
    assert db_session.get(models.User, seller_id).deleted_at is not None
    assert db_session.get(models.Product, product_id).winning_bid_id == winning_bid_id
    assert db_session.get(models.User, bidder_id).deleted_at is None


def test_delete_admin_keeps_reviewed_requests(
    client, db_session, make_user, make_product, auth
):
    owner, admin = make_user(), make_user("admin")
    admin_id = admin.id
    product = make_product(owner)
    request = models.ProductStatusRequest(
        product_id=product.id,
        requested_by=owner.id,
        requested_status=ProductStatus.ACTIVE,
        reviewed_by=admin.id,
    )
    db_session.add(request)
    db_session.flush()
    request_id = request.id

    response = client.delete("/users/me", headers=auth(admin))
    assert response.status_code == 202, response.text
    db_session.expire_all()
    kept = db_session.get(models.ProductStatusRequest, request_id)
    assert kept is not None
    assert kept.reviewed_by == admin_id


def test_delete_account_with_password_reset_token(client, db_session, make_user, auth):
    user = make_user()
    db_session.add(
        models.PasswordResetToken(
            user_id=user.id,
            token_hash=uuid.uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
    )
    db_session.flush()
    assert client.delete("/users/me", headers=auth(user)).status_code == 202


def test_deleted_user_is_logged_out(client, db_session, make_user, auth):
    user = make_user()
    user_id = user.id
    headers = auth(user)
    refresh_token = client.post(
        "/auth/", data={"username": user.username, "password": "TestPassword123!"}
    ).json()["refresh_token"]

    assert client.delete("/users/me", headers=headers).status_code == 202

    assert client.get("/users/me", headers=headers).status_code == 401
    assert (
        client.post("/auth/refresh", json={"refresh_token": refresh_token}).status_code
        == 401
    )
    db_session.expire_all()
    tokens = db_session.query(models.RefreshToken).filter_by(user_id=user_id).all()
    assert tokens and all(token.revoked_at is not None for token in tokens)


@pytest.mark.parametrize("status", [ProductStatus.ACTIVE, ProductStatus.CLOSED])
def test_cannot_delete_account_with_unsettled_auction(
    client, db_session, make_user, make_product, make_bid, auth, status
):
    seller, bidder = make_user(), make_user()
    seller_id = seller.id
    draft = make_product(seller)
    draft_id = draft.id
    make_bid(make_product(seller, status), bidder, 600)

    response = client.delete("/users/me", headers=auth(seller))
    assert response.status_code == 409, response.text

    # NOTHING IS DELETED, NOT EVEN THE PRODUCTS CHECKED BEFORE THE BLOCKED ONE
    db_session.expire_all()
    assert db_session.get(models.User, seller_id).deleted_at is None
    assert db_session.get(models.Product, draft_id).deleted_at is None


def test_admin_cannot_delete_user_with_unsettled_auction(
    client, make_user, make_product, make_bid, auth
):
    admin, seller, bidder = make_user("admin"), make_user(), make_user()
    make_bid(make_product(seller, ProductStatus.ACTIVE), bidder, 600)
    assert client.delete(f"/users/{seller.id}", headers=auth(admin)).status_code == 409


def test_delete_account_removes_products_without_bids(
    client, db_session, make_user, make_product, auth
):
    seller = make_user()
    seller_id = seller.id
    draft = make_product(seller)
    active = make_product(seller, ProductStatus.ACTIVE)
    closed = make_product(seller, ProductStatus.CLOSED)
    product_ids = [draft.id, active.id, closed.id]
    request_id = client.post(
        f"/products/{draft.id}/status-request",
        params={"request": "active"},
        headers=auth(seller),
    ).json()["id"]

    response = client.delete("/users/me", headers=auth(seller))
    assert response.status_code == 202, response.text

    db_session.expire_all()
    for product_id in product_ids:
        assert db_session.get(models.Product, product_id).deleted_at is not None
    status_request = db_session.get(models.ProductStatusRequest, request_id)
    assert status_request.approval_status == ApprovalStatus.CANCELLED
    assert status_request.reviewed_by == seller_id


def test_delete_account_keeps_rejected_product_with_bids(
    client, db_session, make_user, make_product, make_bid, auth
):
    seller, bidder = make_user(), make_user()
    product = make_product(seller, ProductStatus.REJECTED)
    product_id = product.id
    make_bid(product, bidder, 600)

    response = client.delete("/users/me", headers=auth(seller))
    assert response.status_code == 202, response.text

    db_session.expire_all()
    assert db_session.get(models.Product, product_id).deleted_at is None
