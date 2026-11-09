import pytest

from app import models
from app.enums import ApprovalStatus, ProductStatus


def test_create_product(client, make_user, auth, db_session):
    owner = make_user()
    response = client.post(
        "/products/",
        json={"name": "Camera", "description": "New", "start_price": 100},
        headers=auth(owner),
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["current_price"] == 100
    assert data["owner_id"] == owner.id
    assert db_session.get(models.Product, data["id"]) is not None


def test_create_requires_login(client):
    assert (
        client.post("/products/", json={"name": "X", "start_price": 100}).status_code
        == 401
    )


def test_invalid_product_price(client, make_user, auth):
    assert (
        client.post(
            "/products/",
            json={"name": "X", "start_price": 0},
            headers=auth(make_user()),
        ).status_code
        == 422
    )


def test_get_product_by_id(client, make_user, make_product):
    product = make_product(make_user(), ProductStatus.ACTIVE)
    response = client.get(f"/products/{product.id}")
    assert response.status_code == 200, response.text
    assert response.json()["id"] == product.id


def test_get_private_product_by_id(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner, ProductStatus.DRAFT)
    url = f"/products/{product.id}"
    assert client.get(url, headers=auth(owner)).status_code == 200
    assert client.get(url, headers=auth(make_user("admin"))).status_code == 200
    # NON-OWNERS GET THE SAME 404 AS A MISSING PRODUCT
    assert client.get(url).status_code == 404
    assert client.get(url, headers=auth(make_user())).status_code == 404


def test_get_missing_product(client):
    assert client.get("/products/999999").status_code == 404


def test_get_my_products(client, make_user, make_product, auth):
    owner, other = make_user(), make_user()
    product = make_product(owner)
    make_product(other)
    response = client.get("/products/my", headers=auth(owner))
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()["items"]] == [product.id]
    assert response.json()["total"] == 1


def test_get_my_products_empty(client, make_user, auth):
    response = client.get("/products/my", headers=auth(make_user()))
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_get_products_by_status(client, make_user, make_product):
    product = make_product(make_user(), ProductStatus.ACTIVE)
    response = client.get("/products/status/active")
    assert response.status_code == 200, response.text
    assert product.id in [row["id"] for row in response.json()["items"]]


def test_private_status_returns_only_own_products(
    client, make_user, make_product, auth
):
    owner, admin = make_user(), make_user("admin")
    own = make_product(owner, ProductStatus.REJECTED)
    make_product(admin, ProductStatus.REJECTED)

    response = client.get("/products/status/rejected", headers=auth(owner))
    assert response.status_code == 200, response.text
    assert [row["id"] for row in response.json()["items"]] == [own.id]

    # ADMINS ONLY SEE THEIR OWN HERE TOO, EVERYONE'S IS IN THE ADMIN DASHBOARD
    response = client.get("/products/status/rejected", headers=auth(admin))
    assert own.id not in [row["id"] for row in response.json()["items"]]


def test_private_status_empty_message(client, make_user, auth):
    response = client.get("/products/status/draft", headers=auth(make_user()))
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_private_status_requires_login(client):
    assert client.get("/products/status/draft").status_code == 401


def test_admin_sees_all_products_by_status(client, make_user, make_product, auth):
    products = [make_product(make_user(), ProductStatus.DRAFT) for _ in range(2)]
    response = client.get(
        "/admin/products/status/draft", headers=auth(make_user("admin"))
    )
    assert response.status_code == 200, response.text
    ids = [row["id"] for row in response.json()["items"]]
    assert all(product.id in ids for product in products)


def test_update_product(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner)
    response = client.put(
        f"/products/{product.id}",
        json={"name": "Updated", "description": "Changed", "start_price": 200},
        headers=auth(owner),
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Updated"


def test_patch_product(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner)
    response = client.patch(
        f"/products/{product.id}", json={"name": "Patched"}, headers=auth(owner)
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Patched"


def test_delete_product(client, db_session, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner)
    product_id = product.id

    response = client.delete(
        f"/products/{product_id}",
        headers=auth(owner),
    )

    # Your endpoint returns HTTP 202
    assert response.status_code == 202, response.text
    assert response.json() == {"detail": "Product deleted successfully."}

    # Refresh the test session's cached objects
    db_session.expire_all()

    # Verify the product was soft-deleted: the row stays but the API hides it
    deleted_product = db_session.get(models.Product, product_id)

    assert deleted_product.deleted_at is not None
    assert client.get(f"/products/{product_id}", headers=auth(owner)).status_code == 404


def test_delete_product_cancels_pending_request(
    client, db_session, make_user, make_product, auth
):
    owner = make_user()
    owner_id = owner.id
    admin = make_user("admin")
    product = make_product(owner)
    request_id = client.post(
        f"/products/{product.id}/status-request",
        params={"request": "active"},
        headers=auth(owner),
    ).json()["id"]

    response = client.delete(f"/products/{product.id}", headers=auth(owner))
    assert response.status_code == 202, response.text

    db_session.expire_all()
    status_request = db_session.get(models.ProductStatusRequest, request_id)
    assert status_request.approval_status == ApprovalStatus.CANCELLED
    assert status_request.reviewed_by == owner_id
    assert status_request.reviewed_at is not None

    pending = client.get("/admin/status-request/pending", headers=auth(admin))
    assert request_id not in [item["id"] for item in pending.json()["items"]]


def test_admin_list_hides_deleted_products(client, make_user, make_product, auth):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner)
    product_id = product.id
    client.delete(f"/products/{product_id}", headers=auth(owner))

    response = client.get("/admin/products/status/draft", headers=auth(admin))
    assert product_id not in [item["id"] for item in response.json()["items"]]


def test_request_activation(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner)
    response = client.post(
        f"/products/{product.id}/status-request",
        params={"request": "active"},
        headers=auth(owner),
    )
    assert response.status_code == 201, response.text
    assert response.json()["requested_status"] == "active"
    assert (
        client.post(
            f"/products/{product.id}/status-request",
            params={"request": "active"},
            headers=auth(owner),
        ).status_code
        == 409
    )


def test_nonowner_cannot_request_activation(client, make_user, make_product, auth):
    owner, other = make_user(), make_user()
    product = make_product(owner)
    assert (
        client.post(
            f"/products/{product.id}/status-request",
            params={"request": "active"},
            headers=auth(other),
        ).status_code
        == 403
    )


def test_cannot_request_close(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner)
    assert (
        client.post(
            f"/products/{product.id}/status-request",
            params={"request": "closed"},
            headers=auth(owner),
        ).status_code
        == 403
    )


def test_my_products_pagination(client, make_user, make_product, auth):
    owner = make_user()
    ids = sorted(make_product(owner).id for _ in range(3))

    first = client.get("/products/my?limit=2&page=1", headers=auth(owner)).json()
    assert [row["id"] for row in first["items"]] == ids[:2]
    assert first["total"] == 3

    second = client.get("/products/my?limit=2&page=2", headers=auth(owner)).json()
    assert [row["id"] for row in second["items"]] == ids[2:]
    assert second["total"] == 3

    past_end = client.get("/products/my?limit=2&page=3", headers=auth(owner))
    assert past_end.status_code == 200
    assert past_end.json() == {"items": [], "total": 3}


def test_status_list_pagination_total(client, make_user, make_product):
    owner = make_user()
    for _ in range(3):
        make_product(owner, ProductStatus.ACTIVE)
    body = client.get("/products/status/active?limit=1").json()
    assert len(body["items"]) == 1
    assert body["total"] >= 3


def test_admin_list_pagination(client, make_user, make_product, auth):
    admin = make_user("admin")
    for _ in range(3):
        make_product(make_user(), ProductStatus.DRAFT)
    body = client.get(
        "/admin/products/status/draft?limit=2&page=1", headers=auth(admin)
    ).json()
    assert len(body["items"]) == 2
    assert body["total"] >= 3


def test_admin_pending_pagination(client, make_user, make_product, auth):
    admin = make_user("admin")
    for _ in range(2):
        owner = make_user()
        product = make_product(owner)
        client.post(
            f"/products/{product.id}/status-request",
            params={"request": "active"},
            headers=auth(owner),
        )
    body = client.get(
        "/admin/status-request/pending?limit=1", headers=auth(admin)
    ).json()
    assert len(body["items"]) == 1
    assert body["total"] >= 2


@pytest.mark.parametrize("query", ["page=0", "limit=0", "limit=21"])
@pytest.mark.parametrize("path", ["/products/my", "/products/status/active"])
def test_invalid_pagination_products(client, make_user, auth, path, query):
    response = client.get(f"{path}?{query}", headers=auth(make_user()))
    assert response.status_code == 422
