from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app import models
from app.enums import ProductStatus


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
    ):
        return (
            self._query(include_deleted)
            .filter(models.Product.owner_id == owner_id)
            .all()
        )

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
    ):
        query = self._query(include_deleted).filter(
            models.Product.status == product_status
        )

        if owner_id is not None:
            query = query.filter(models.Product.owner_id == owner_id)

        return query.all()

    def get_all_by_status(self, product_status: ProductStatus):
        return (
            self._query()
            .filter(models.Product.status == product_status)
            .order_by(models.Product.id.asc())
            .all()
        )

    def create(self, product: models.Product):
        self.db.add(product)
        self.db.flush()
        return product

    def softdelete(self, product: models.Product):
        product.deleted_at = datetime.now(UTC)
        self.db.flush()
        return product

    def get_by_id_for_delete(self, product_id: int):
        return (
            self._query()
            .filter(models.Product.id == product_id)
            .with_for_update()
            .first()
        )

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
            setattr(product, key, value)

        self.db.flush()
        return product

    def get_by_id_for_status_change(self, product_id: int):
        return (
            self._query()
            .filter(models.Product.id == product_id)
            .with_for_update()
            .first()
        )

    def create_bulk(self, products: list[models.Product]):
        self.db.add_all(products)
        self.db.flush()
        return products
