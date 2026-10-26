# Auction API pytest suite

## Setup

Use a dedicated PostgreSQL database **auctionapi_test**. Never use a production or development database.

Set `SQLALCHEMY_TEST_URL` in `.env` to a dedicated test database; keep `SQLALCHEMY_URL` pointed at development. Run:

```bash
uv add --dev pytest httpx
uv run pytest -v tests --ignore=tests/test_concurrency.py
uv run pytest -v tests/test_concurrency.py
```

The test fixtures create missing tables but **do not drop existing tables or truncate the database**. Normal tests use an outer transaction and rollback after each test. Existing data in the test database may affect tests that assume missing IDs (999999). Prefer a clean dedicated test DB.

The concurrency test uses separate real PostgreSQL connections and committed records, then cleans up only records it created. Run it separately and do not run concurrently with tests using global dependency overrides.

The suite does not launch Celery workers or send real emails; the forgot-password email sender is monkeypatched. Make sure your own external Celery worker/beat processes are not pointed at the test database while running tests.

Some tests intentionally expose existing application bugs. A failure means inspect the assertion and implementation; do not change an assertion solely to force a pass. No PostgreSQL server was available to execute these tests during generation.
