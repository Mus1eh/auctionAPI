"""update() only touches the fields a repository lists, so a stray key from a caller
cannot rewrite ownership, ids or deletion state."""

import pytest

from app import models
from app.enums import ApprovalStatus, ProductStatus
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository


@pytest.mark.parametrize(
    "field", ["id", "owner_id", "winning_bid_id", "deleted_at", "not_a_column"]
)
def test_product_update_refuses_protected_fields(
    db_session, make_user, make_product, field
):
    owner = make_user()
    product = make_product(owner)

    with pytest.raises(ValueError, match=field):
        ProductRepository(db_session).update(product, {field: 1})

    assert product.owner_id == owner.id
    assert product.deleted_at is None


def test_product_update_changes_allowed_fields(db_session, make_user, make_product):
    product = make_product(make_user())

    updated = ProductRepository(db_session).update(
        product, {"name": "Renamed", "status": ProductStatus.REJECTED}
    )

    assert (updated.name, updated.status) == ("Renamed", ProductStatus.REJECTED)


@pytest.mark.parametrize(
    "field", ["id", "product_id", "requested_by", "requested_status", "created_at"]
)
def test_status_request_update_refuses_protected_fields(
    db_session, make_user, make_product, field
):
    owner = make_user()
    request = models.ProductStatusRequest(
        product_id=make_product(owner).id,
        requested_by=owner.id,
        requested_status=ProductStatus.ACTIVE,
    )
    db_session.add(request)
    db_session.flush()

    with pytest.raises(ValueError, match=field):
        ProductStatusRequestRepository(db_session).update(request, {field: 1})

    assert request.requested_by == owner.id


def test_status_request_update_changes_review_fields(
    db_session, make_user, make_product
):
    admin, owner = make_user("admin"), make_user()
    request = models.ProductStatusRequest(
        product_id=make_product(owner).id,
        requested_by=owner.id,
        requested_status=ProductStatus.ACTIVE,
    )
    db_session.add(request)
    db_session.flush()

    updated = ProductStatusRequestRepository(db_session).update(
        request, {"approval_status": ApprovalStatus.APPROVED, "reviewed_by": admin.id}
    )

    assert (updated.approval_status, updated.reviewed_by) == (
        ApprovalStatus.APPROVED,
        admin.id,
    )
