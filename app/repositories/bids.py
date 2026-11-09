from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models


class BidRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, bid: models.Bids):
        self.db.add(bid)
        self.db.flush()
        return bid

    def get_bids_for_product(self, product_id: int, offset: int, limit: int):
        query = (
            self.db.query(models.Bids)
            .filter(models.Bids.product_id == product_id)
            .order_by(models.Bids.id.desc())
        )
        total = query.count()
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all(), total

    def get_highest_by_product(self, product_id: int):
        return (
            self.db.query(models.Bids)
            .filter(models.Bids.product_id == product_id)
            .order_by(models.Bids.amount.desc(), models.Bids.id.desc())
            .first()
        )

    def count_by_product(self, product_id: int) -> int:
        return (
            self.db.query(func.count(models.Bids.id))
            .filter(models.Bids.product_id == product_id)
            .scalar()
        )

    def get_latest_by_product(self, product_id: int):
        return (
            self.db.query(models.Bids)
            .filter(models.Bids.product_id == product_id)
            .order_by(models.Bids.id.desc())
            .first()
        )
