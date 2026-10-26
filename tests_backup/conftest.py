import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app

load_dotenv()

TEST_DATABASE_URL = os.environ["SQLALCHEMY_TEST_URL"]

# Safety check: never point pytest at our development database.
test_url = make_url(TEST_DATABASE_URL)

if test_url.database != "auctionapi_test":
    raise RuntimeError("Tests must use the auctionapi_test database!")

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session")
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def db_session(setup_database):
    connection = test_engine.connect()
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
