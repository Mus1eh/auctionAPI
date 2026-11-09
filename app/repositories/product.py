from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models
from app.enums import ProductStatus

ALLOWED_FIELDS = {
    "name",
    "description",
    "start_price",
    "current_price",
    "status",
    "auction_started_at",
    "auction_ends_at",
}


class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def _query(self, include_deleted: bool = False):
        query = self.db.query(models.Product)

        if not include_deleted:
            query = query.filter(models.Product.deleted_at.is_(None))

        return query

    def get_by_id(
        self,
        product_id: int,
        include_deleted: bool = False,
    ):
        return (
            self._query(include_deleted).filter(models.Product.id == product_id).first()
        )

    def get_by_owner(
        self,
        owner_id: int,
        include_deleted: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ):

        query = (
            self._query(include_deleted)
            .filter(models.Product.owner_id == owner_id)
            .order_by(models.Product.id.asc())
        )
        total = query.count()
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all(), total

    def get_by_owner_for_update(self, owner_id: int):
        return (
            self._query()
            .filter(models.Product.owner_id == owner_id)
            .order_by(models.Product.id.asc())
            .with_for_update()
            .all()
        )

    def get_by_status(
        self,
        product_status: ProductStatus,
        owner_id: int | None = None,
        include_deleted: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ):
        query = (
            self._query(include_deleted)
            .filter(models.Product.status == product_status)
            .order_by(models.Product.id.asc())
        )

        if owner_id is not None:
            query = query.filter(models.Product.owner_id == owner_id)

        total = query.count()

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all(), total

    def get_all_by_status(
        self,
        product_status: ProductStatus,
        limit: int | None = None,
        offset: int | None = None,
    ):
        query = (
            self._query()
            .filter(models.Product.status == product_status)
            .order_by(models.Product.id.asc())
        )
        total = query.count()

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all(), total

    def create(self, product: models.Product):
        self.db.add(product)
        self.db.flush()
        return product

    def softdelete(self, product: models.Product):
        product.deleted_at = datetime.now(UTC)
        self.db.flush()
        return product

    def restore(self, product: models.Product):
        product.deleted_at = None
        self.db.flush()
        return product

    def get_by_id_for_update(self, product_id: int):
        return (
            self._query()
            .filter(models.Product.id == product_id)
            .with_for_update()
            .first()
        )

    def has_bids(self, product_id: int) -> bool:
        return (
            self.db.query(models.Bids.id)
            .filter(models.Bids.product_id == product_id)
            .first()
            is not None
        )

    def update(self, product: models.Product, data: dict):
        for key, value in data.items():
            if key not in ALLOWED_FIELDS:
                raise ValueError(f"Field '{key}' is not allowed to be updated.")

            setattr(product, key, value)

        self.db.flush()
        return product

    def create_bulk(self, products: list[models.Product]):
        self.db.add_all(products)
        self.db.flush()
        return products

    def get_expired_active_for_update(self, now: datetime):
        return (
            self._query()
            .filter(
                models.Product.status == ProductStatus.ACTIVE,
                models.Product.auction_ends_at <= now,
            )
            .with_for_update(skip_locked=True)
            .all()
        )
