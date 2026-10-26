import pytest

from app import models
from app.enums import ProductStatus


def test_bid_requires_login(client):
    assert client.post("/bids/999999", json={"amount": 600}).status_code == 401


def test_missing_product(client, make_user, auth):
    bidder = make_user()
    response = client.post("/bids/999999", json={"amount": 600}, headers=auth(bidder))
    assert response.status_code == 404


@pytest.mark.parametrize("amount", [0, -1])
def test_invalid_bid_amount(client, make_user, auth, amount):
    assert (
        client.post(
            "/bids/999999", json={"amount": amount}, headers=auth(make_user())
        ).status_code
        == 422
    )


def test_successful_bid_updates_price(
    client, db_session, make_user, make_product, auth
):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.ACTIVE)
    response = client.post(
        f"/bids/{product.id}", json={"amount": 600}, headers=auth(bidder)
    )
    assert response.status_code == 201, response.text
    assert response.json()["amount"] == 600
    db_session.refresh(product)
    assert product.current_price == 600
    assert db_session.query(models.Bids).filter_by(product_id=product.id).count() == 1


@pytest.mark.parametrize("amount", [499, 500])
def test_bid_must_exceed_current_price(client, make_user, make_product, auth, amount):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.ACTIVE)
    assert (
        client.post(
            f"/bids/{product.id}", json={"amount": amount}, headers=auth(bidder)
        ).status_code
        == 409
    )


def test_owner_cannot_bid(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner, ProductStatus.ACTIVE)
    assert (
        client.post(
            f"/bids/{product.id}", json={"amount": 600}, headers=auth(owner)
        ).status_code
        == 403
    )


@pytest.mark.parametrize(
    "status",
    [
        ProductStatus.DRAFT,
        ProductStatus.CLOSED,
        ProductStatus.SOLD,
        ProductStatus.REJECTED,
    ],
)
def test_inactive_auction_rejects_bid(client, make_user, make_product, auth, status):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, status)
    assert (
        client.post(
            f"/bids/{product.id}", json={"amount": 600}, headers=auth(bidder)
        ).status_code
        == 409
    )


def test_expired_auction_rejects_bid(client, make_user, make_product, auth):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.ACTIVE, ended=True)
    assert (
        client.post(
            f"/bids/{product.id}", json={"amount": 600}, headers=auth(bidder)
        ).status_code
        == 409
    )


def test_list_bids_and_pagination(client, make_user, make_product, make_bid):
    owner, bidder = make_user(), make_user()
    product = make_product(owner)
    make_bid(product, bidder, 600)
    make_bid(product, bidder, 700)
    response = client.get(f"/bids/{product.id}?page=1&limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["amount"] == 700
    assert client.get(f"/bids/{product.id}?page=2&limit=1").json()[0]["amount"] == 600


def test_list_bids_missing_product(client):
    assert client.get("/bids/999999").status_code == 404


@pytest.mark.parametrize("query", ["page=0", "limit=0", "limit=21"])
def test_invalid_pagination(client, query):
    assert client.get(f"/bids/1?{query}").status_code == 422
