"""PostgreSQL-backed fixtures. NEVER point SQLALCHEMY_TEST_URL at real data."""

import os
import uuid
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

load_dotenv()
TEST_DATABASE_URL = os.environ.get("SQLALCHEMY_TEST_URL", "")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "Set SQLALCHEMY_TEST_URL to a dedicated PostgreSQL test database"
    )
test_url = make_url(TEST_DATABASE_URL)
if (
    test_url.get_backend_name() != "postgresql"
    or test_url.database != "auctionapi_test"
):
    raise RuntimeError(
        "Refusing tests: SQLALCHEMY_TEST_URL must target PostgreSQL auctionapi_test"
    )
if os.getenv("SQLALCHEMY_URL"):
    dev_url = make_url(os.environ["SQLALCHEMY_URL"])
    if (test_url.host, test_url.port, test_url.database) == (
        dev_url.host,
        dev_url.port,
        dev_url.database,
    ):
        raise RuntimeError("Test and development databases must be different")

from app import models
from app.core.database import Base, get_db
from app.core.security import Hash, create_access_token
from app.dependencies import get_rate_limiter
from app.enums import ProductStatus
from app.main import app
from app.seeders.rbac import PERMISSIONS, ROLE_PERMISSIONS, ROLES

engine = create_engine(TEST_DATABASE_URL)


class NoRateLimiter:
    """Never refuses anything. The whole suite calls the API from one IP, so real
    limits would turn ordinary tests into 429s. test_rate_limit.py swaps in a real one."""

    def check(self, scope, key, rule):
        pass

    def ensure_allowed(self, scope, key, rule):
        pass

    def record(self, scope, key, rule):
        pass

    def clear(self, scope, key, rule):
        pass


@pytest.fixture(autouse=True)
def rate_limiting_off():
    app.dependency_overrides[get_rate_limiter] = NoRateLimiter
    yield
    app.dependency_overrides.pop(get_rate_limiter, None)


@pytest.fixture(scope="session", autouse=True)
def schema():
    # Rebuild from the current models so new columns reach the test database.
    # CASCADE because products and bids reference each other, which drop_all can't order.
    with engine.begin() as conn:
        for table_name in Base.metadata.tables:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture
def db_session(schema):
    with engine.connect() as conn:
        outer = conn.begin()
        db = Session(
            bind=conn, join_transaction_mode="create_savepoint", autoflush=False
        )
        try:
            yield db
        finally:
            db.close()
            outer.rollback()


@pytest.fixture
def client(db_session):
    connection = db_session.connection()

    def override_db():
        with Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            autoflush=False,
        ) as request_db:
            yield request_db

    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def roles(db_session):
    """Roles, permissions and their links, exactly as the seeder defines them."""
    permissions = {}
    for name in PERMISSIONS:
        permission = db_session.query(models.Permission).filter_by(name=name).first()
        permissions[name] = permission or models.Permission(name=name)
        db_session.add(permissions[name])

    for role_name in ROLES:
        role = db_session.query(models.Role).filter_by(name=role_name).first()
        if not role:
            role = models.Role(name=role_name)
            db_session.add(role)
        role.permissions = [permissions[n] for n in ROLE_PERMISSIONS[role_name]]
    db_session.flush()


@pytest.fixture
def make_user(db_session, roles):
    def create(role="user", password="TestPassword123!"):
        ident = uuid.uuid4().hex[:12]
        user = models.User(
            username=f"u_{ident}",
            email=f"pytest_{uuid4().hex}@example.com",
            password=Hash.crypt_password(password),
        )
        user.roles.append(db_session.query(models.Role).filter_by(name=role).one())
        db_session.add(user)
        db_session.flush()
        return user

    return create


@pytest.fixture
def task_sessions(db_session, monkeypatch):
    """Celery tasks open their own sessions; point them at the test transaction."""
    from app.worker import tasks

    connection = db_session.connection()

    def factory():
        return Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            autoflush=False,
        )

    monkeypatch.setattr(tasks, "sessionLocal", factory)


@pytest.fixture
def eager_celery(task_sessions):
    """Run queued tasks inline and keep their results in memory, so no Redis is needed."""
    from app.worker.celery_app import celery_app

    previous = {
        key: celery_app.conf[key]
        for key in ("task_always_eager", "task_store_eager_result", "result_backend")
    }
    previous_backend = getattr(celery_app._local, "backend", None)
    celery_app.conf.update(
        task_always_eager=True,
        task_store_eager_result=True,
        result_backend="cache+memory://",
    )
    celery_app._local.backend = None
    try:
        yield celery_app
    finally:
        celery_app.conf.update(previous)
        celery_app._local.backend = previous_backend


@pytest.fixture
def auth():
    def headers(user):
        token = create_access_token({"sub": user.username})
        return {"Authorization": f"Bearer {token}"}

    return headers


@pytest.fixture
def make_product(db_session):
    def create(owner, status=ProductStatus.DRAFT, price=500, ended=False):
        now = datetime.now(UTC)
        product = models.Product(
            name="Test auction",
            description="For pytest",
            start_price=price,
            current_price=price,
            owner_id=owner.id,
            status=status,
            auction_started_at=now - timedelta(hours=2)
            if status != ProductStatus.DRAFT
            else None,
            auction_ends_at=(
                now - timedelta(seconds=1) if ended else now + timedelta(hours=1)
            )
            if status != ProductStatus.DRAFT
            else None,
        )
        db_session.add(product)
        db_session.flush()
        return product

    return create


@pytest.fixture
def make_bid(db_session):
    def create(product, bidder, amount):
        bid = models.Bids(product_id=product.id, user_id=bidder.id, amount=amount)
        db_session.add(bid)
        product.current_price = amount
        db_session.flush()
        return bid

    return create
