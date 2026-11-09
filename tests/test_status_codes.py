"""What each status code means in this API, and one wording per missing thing.

404 missing or hidden, 409 the item's current state forbids the request,
403 the caller is not allowed, 400 the request itself is wrong.
"""

import pytest

from app.enums import ProductStatus

MISSING = 999999


def missing_product_calls(client, auth, user, admin):
    return {
        "get product": lambda: client.get(f"/products/{MISSING}"),
        "update product": lambda: client.put(
            f"/products/{MISSING}",
            json={"name": "x", "start_price": 5},
            headers=auth(user),
        ),
        "patch product": lambda: client.patch(
            f"/products/{MISSING}", json={"name": "x"}, headers=auth(user)
        ),
        "delete product": lambda: client.delete(
            f"/products/{MISSING}", headers=auth(user)
        ),
        "request go live": lambda: client.post(
            f"/products/{MISSING}/status-request",
            params={"request": "active"},
            headers=auth(user),
        ),
        "restore draft": lambda: client.post(
            f"/products/{MISSING}/restore-draft", headers=auth(user)
        ),
        "list bids": lambda: client.get(f"/bids/{MISSING}"),
        "place bid": lambda: client.post(
            f"/bids/{MISSING}", json={"amount": 10}, headers=auth(user)
        ),
        "decide bid": lambda: client.post(
            f"/bids/{MISSING}/approve",
            params={"request": "approve"},
            headers=auth(user),
        ),
        "admin change status": lambda: client.post(
            f"/admin/products/{MISSING}/status/active", headers=auth(admin)
        ),
    }


def test_a_missing_product_is_reported_the_same_way_everywhere(client, make_user, auth):
    user, admin = make_user(), make_user("admin")
    for name, call in missing_product_calls(client, auth, user, admin).items():
        response = call()
        assert response.status_code == 404, name
        assert response.json() == {"detail": "Product is not found."}, name


def test_a_missing_user_and_status_request_have_one_wording_too(
    client, make_user, auth
):
    admin, superadmin = make_user("admin"), make_user("superadmin")

    response = client.get(f"/users/{MISSING}", headers=auth(admin))
    assert (response.status_code, response.json()) == (
        404,
        {"detail": "User is not found."},
    )
    response = client.patch(
        f"/admin/users/{MISSING}/role",
        json={"role_name": "admin"},
        headers=auth(superadmin),
    )
    assert (response.status_code, response.json()) == (
        404,
        {"detail": "User is not found."},
    )
    for action in ("approve", "reject"):
        response = client.patch(
            f"/admin/status-requests/{MISSING}/{action}", headers=auth(admin)
        )
        assert (response.status_code, response.json()) == (
            404,
            {"detail": "Status request is not found."},
        )


# --- 409: the request is fine, the item's state does not allow it ---------


@pytest.mark.parametrize(
    ("status", "requested", "message"),
    [
        (
            ProductStatus.ACTIVE,
            "active",
            "The requested status is the same as the current status.",
        ),
        (ProductStatus.SOLD, "active", "Invalid product status transition."),
    ],
)
def test_asking_for_a_status_the_product_cannot_take_is_a_conflict(
    client, make_user, make_product, auth, status, requested, message
):
    owner = make_user()
    product = make_product(owner, status)

    response = client.post(
        f"/products/{product.id}/status-request",
        params={"request": requested},
        headers=auth(owner),
    )

    assert response.status_code == 409
    assert response.json() == {"detail": message}


def test_a_pending_request_is_still_reported_as_pending(
    client, make_user, make_product, auth
):
    owner = make_user()
    product = make_product(owner)
    url = f"/products/{product.id}/status-request"
    assert (
        client.post(url, params={"request": "active"}, headers=auth(owner)).status_code
        == 201
    )

    response = client.post(url, params={"request": "active"}, headers=auth(owner))

    assert response.status_code == 409
    assert response.json() == {
        "detail": "There is already a pending request for this product."
    }


def test_same_status_is_the_same_conflict_for_admins(
    client, make_user, make_product, auth
):
    owner, admin = make_user(), make_user("admin")
    product = make_product(owner, ProductStatus.ACTIVE)

    response = client.post(
        f"/admin/products/{product.id}/status/active", headers=auth(admin)
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "The requested status is the same as the current status."
    }


def test_deciding_a_sold_auction_again_is_a_conflict_not_a_permission_error(
    client, make_user, make_product, make_bid, auth
):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.SOLD)
    make_bid(product, bidder, 600)

    response = client.post(
        f"/bids/{product.id}/approve",
        params={"request": "approve"},
        headers=auth(owner),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Bidding has already been approved for this product."
    }


# --- 403: who you are decides, not the item's state ------------------------


def test_a_stranger_deciding_an_auction_is_forbidden(
    client, make_user, make_product, make_bid, auth
):
    owner, bidder, stranger = make_user(), make_user(), make_user()
    product = make_product(owner, ProductStatus.CLOSED)
    make_bid(product, bidder, 600)

    response = client.post(
        f"/bids/{product.id}/approve",
        params={"request": "approve"},
        headers=auth(stranger),
    )

    assert response.status_code == 403
