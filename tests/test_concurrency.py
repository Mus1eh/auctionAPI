"""Real PostgreSQL concurrency test. Does NOT use the shared rollback connection.

Creates committed test records, issues concurrent HTTP requests on separate DB
connections, and deletes only those records afterward.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.enums import ProductStatus
from app.hashing import Hash
from app.main import app
from app.oauth2 import create_access_token
from tests.conftest import engine


def test_two_simultaneous_identical_bids(schema):
    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    unique = uuid.uuid4().hex[:12]
    user_ids = []
    product_id = None
    with Session(engine) as db:
        for name in ("user",):
            if not db.query(models.Role).filter_by(name=name).first():
                db.add(models.Role(name=name))
        db.flush()
        for index in range(3):
            user = models.User(
                username=f"con_{index}_{unique}",
                email=f"con_{index}_{unique}@example.com",
                password=Hash.crypt_password("TestPassword123!"),
                role_name="user",
            )
            db.add(user)
            db.flush()
            user_ids.append(user.id)
        now = datetime.now(UTC)
        product = models.Product(
            name="Concurrent auction",
            start_price=500,
            current_price=500,
            owner_id=user_ids[0],
            status=ProductStatus.ACTIVE,
            auction_started_at=now,
            auction_ends_at=now + timedelta(hours=1),
        )
        db.add(product)
        db.flush()
        product_id = product.id
        names = [db.get(models.User, uid).username for uid in user_ids[1:]]
        db.commit()

    barrier = Barrier(2)

    def bid(username):
        token = create_access_token({"sub": username})
        with TestClient(app) as client:
            barrier.wait(timeout=10)
            response = client.post(
                f"/bids/{product_id}",
                json={"amount": 600},
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.status_code, response.text

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(bid, names))
        assert sorted(status for status, _ in results) == [201, 409], results
        with Session(engine) as db:
            product = db.get(models.Product, product_id)
            assert product.current_price == 600
            assert db.query(models.Bids).filter_by(product_id=product_id).count() == 1
    finally:
        app.dependency_overrides.pop(get_db, None)
        with Session(engine) as db:
            if product_id is not None:
                product = db.get(models.Product, product_id)
                if product:
                    db.delete(product)
                    db.flush()
            for uid in user_ids:
                user = db.get(models.User, uid)
                if user:
                    db.delete(user)
            db.commit()
