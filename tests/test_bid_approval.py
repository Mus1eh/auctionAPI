import pytest

from app import models
from app.enums import ProductStatus


def test_only_owner_can_approve(client, make_user, make_product, make_bid, auth):
    owner, bidder, stranger = make_user(), make_user(), make_user()
    product = make_product(owner, ProductStatus.CLOSED)
    make_bid(product, bidder, 600)
    assert (
        client.post(
            f"/bids/{product.id}/approve",
            params={"request": "approve"},
            headers=auth(stranger),
        ).status_code
        == 403
    )


def test_cannot_approve_active_auction(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner, ProductStatus.ACTIVE)
    assert (
        client.post(
            f"/bids/{product.id}/approve",
            params={"request": "approve"},
            headers=auth(owner),
        ).status_code
        == 403
    )


def test_approve_highest_bid(
    client, db_session, make_user, make_product, make_bid, auth
):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.CLOSED)
    winning = make_bid(product, bidder, 700)
    response = client.post(
        f"/bids/{product.id}/approve",
        params={"request": "approve"},
        headers=auth(owner),
    )
    assert response.status_code == 200, response.text
    db_session.refresh(product)
    assert product.status == ProductStatus.SOLD
    assert product.winning_bid_id == winning.id
    assert response.json()["winning_bidder"]["id"] == bidder.id
    assert (
        db_session.query(models.EmailOutbox).filter_by(to_email=bidder.email).count()
        == 1
    )
    assert (
        client.post(
            f"/bids/{product.id}/approve",
            params={"request": "approve"},
            headers=auth(owner),
        ).status_code
        == 403
    )


def test_reject_bid(client, db_session, make_user, make_product, make_bid, auth):
    owner, bidder = make_user(), make_user()
    product = make_product(owner, ProductStatus.CLOSED)
    make_bid(product, bidder, 600)
    response = client.post(
        f"/bids/{product.id}/approve", params={"request": "reject"}, headers=auth(owner)
    )
    assert response.status_code == 200, response.text
    db_session.refresh(product)
    assert product.status == ProductStatus.REJECTED
    assert product.winning_bid_id is None


def test_no_bids_to_approve(client, make_user, make_product, auth):
    owner = make_user()
    product = make_product(owner, ProductStatus.CLOSED)
    assert (
        client.post(
            f"/bids/{product.id}/approve",
            params={"request": "approve"},
            headers=auth(owner),
        ).status_code
        == 404
    )


@pytest.mark.parametrize("value", ["invalid", {"action": "approve"}])
def test_invalid_approval_payload(client, value):
    assert client.post("/bids/1/approve", json=value).status_code in (401, 422)
