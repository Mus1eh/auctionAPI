from app import models
from app.enums import ProductStatus


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
    product = make_product(make_user())
    response = client.get(f"/products/{product.id}")
    assert response.status_code == 200, response.text
    assert response.json()["id"] == product.id


def test_get_missing_product(client):
    assert client.get("/products/999999").status_code == 404


def test_get_my_products(client, make_user, make_product, auth):
    owner, other = make_user(), make_user()
    product = make_product(owner)
    make_product(other)
    response = client.get("/products/my", headers=auth(owner))
    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()] == [product.id]


def test_get_my_products_empty(client, make_user, auth):
    assert client.get("/products/my", headers=auth(make_user())).status_code == 404


def test_get_products_by_status(client, make_user, make_product):
    product = make_product(make_user(), ProductStatus.DRAFT)
    response = client.get("/products/status/draft")
    assert response.status_code == 200, response.text
    assert product.id in [row["id"] for row in response.json()]


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

    # Refresh the test session's cached objects
    db_session.expire_all()

    # Verify the product was actually deleted
    deleted_product = db_session.get(models.Product, product_id)

    assert deleted_product is None


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
