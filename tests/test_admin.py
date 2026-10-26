from app import models
from app.enums import ApprovalStatus, ProductStatus


def test_admin_dashboard_permissions(client, make_user, auth):
    ordinary = make_user()
    assert client.get("/admin/dashboard", headers=auth(ordinary)).status_code == 403
    for role in ("admin", "superadmin"):
        user = make_user(role)
        response = client.get("/admin/dashboard", headers=auth(user))
        assert response.status_code == 200, response.text
        assert response.json()["role"] == role


def test_admin_requires_auth(client):
    assert client.get("/admin/dashboard").status_code == 401


def test_admin_list_pending_requests(client, make_user, make_product, auth):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner)
    assert (
        client.post(
            f"/products/{product.id}/status-request",
            params={"request": "active"},
            headers=auth(owner),
        ).status_code
        == 201
    )
    response = client.get("/admin/status-request/pending", headers=auth(admin))
    assert response.status_code == 200, response.text
    assert any(item["product_id"] == product.id for item in response.json())


def test_approve_activation_request(client, db_session, make_user, make_product, auth):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner)
    created = client.post(
        f"/products/{product.id}/status-request",
        params={"request": "active"},
        headers=auth(owner),
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["id"]
    response = client.patch(
        f"/admin/status-requests/{request_id}/approve", headers=auth(admin)
    )
    assert response.status_code == 200, response.text
    db_session.refresh(product)
    assert product.status == ProductStatus.ACTIVE
    assert product.auction_ends_at is not None
    assert (
        client.patch(
            f"/admin/status-requests/{request_id}/approve", headers=auth(admin)
        ).status_code
        == 409
    )


def test_reject_activation_request(client, db_session, make_user, make_product, auth):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner)
    request_id = client.post(
        f"/products/{product.id}/status-request",
        params={"request": "active"},
        headers=auth(owner),
    ).json()["id"]
    response = client.patch(
        f"/admin/status-requests/{request_id}/reject", headers=auth(admin)
    )
    assert response.status_code == 200, response.text
    assert (
        db_session.get(models.ProductStatusRequest, request_id).approval_status
        == ApprovalStatus.REJECTED
    )
    assert db_session.get(models.Product, product.id).status == ProductStatus.DRAFT


# def test_missing_status_request(client, make_user, auth):
#     admin = make_user("admin")
#     assert (
#         client.patch(
#             "/admin/status-requests/999999/approve", headers=auth(admin)
#         ).status_code
#         == 404
#     )
#     assert (
#         client.patch(
#             "/admin/status-requests/999999/reject", headers=auth(admin)
#         ).status_code
#         == 404
#     )
def test_missing_status_request(client, make_user, auth):
    admin = make_user("admin")

    response1 = client.patch(
        "/admin/status-requests/999999/approve",
        headers=auth(admin),
    )

    print("FIRST:", response1.status_code, response1.text)

    response2 = client.patch(
        "/admin/status-requests/999999/reject",
        headers=auth(admin),
    )

    print("SECOND:", response2.status_code, response2.text)

    assert response1.status_code == 404
    assert response2.status_code == 404


def test_admin_activate_and_close(client, db_session, make_user, make_product, auth):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner)
    activate = client.post(
        f"/admin/products/{product.id}/status/active", headers=auth(admin)
    )
    assert activate.status_code == 200, activate.text
    assert activate.json()["status"] == "active"
    assert (
        client.post(
            f"/admin/products/{product.id}/status/active", headers=auth(admin)
        ).status_code
        == 409
    )
    close = client.post(
        f"/admin/products/{product.id}/status/closed", headers=auth(admin)
    )
    assert close.status_code == 200, close.text
    assert close.json()["status"] == "closed"


def test_admin_invalid_transition(client, make_user, make_product, auth):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner)
    assert (
        client.post(
            f"/admin/products/{product.id}/status/closed", headers=auth(admin)
        ).status_code
        == 409
    )
    assert (
        client.post(
            f"/admin/products/{product.id}/status/sold", headers=auth(admin)
        ).status_code
        == 400
    )


def test_superadmin_changes_role(client, db_session, make_user, auth):
    superadmin, target = make_user("superadmin"), make_user()
    assert (
        client.patch(
            f"/admin/users/{target.id}/role",
            json={"role_name": "admin"},
            headers=auth(make_user("admin")),
        ).status_code
        == 403
    )
    response = client.patch(
        f"/admin/users/{target.id}/role",
        json={"role_name": "admin"},
        headers=auth(superadmin),
    )
    assert response.status_code == 200, response.text
    db_session.expire_all()

    updated_user = db_session.get(models.User, target.id)

    assert updated_user.role_name == "admin"


def test_superadmin_role_validation(client, make_user, auth):
    superadmin, target = make_user("superadmin"), make_user()
    assert (
        client.patch(
            f"/admin/users/{target.id}/role",
            json={"role_name": "superadmin"},
            headers=auth(superadmin),
        ).status_code
        == 400
    )
    assert (
        client.patch(
            f"/admin/users/{superadmin.id}/role",
            json={"role_name": "user"},
            headers=auth(superadmin),
        ).status_code
        == 403
    )
    assert (
        client.patch(
            "/admin/users/999999/role",
            json={"role_name": "user"},
            headers=auth(superadmin),
        ).status_code
        == 404
    )
