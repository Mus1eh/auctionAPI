# Auction API

A REST API for running online auctions, built with **FastAPI**, **PostgreSQL** and **Celery**.

Users list products, an admin approves them, and other users bid during a timed auction. When the auction ends, the owner accepts or rejects the highest bid, and everyone involved gets an email.

## Features

- **Accounts:** sign up, log in with a username or email, JWT access tokens with rotating refresh tokens, log out of one device or all of them.
- **Password management:** change password, plus forgot/reset password by email with single-use tokens. Changing or resetting a password ends every active session.
- **Roles:** `user`, `admin` and `superadmin`. A superadmin can promote users to admin and demote them again.
- **Products:** create, edit, delete, browse by status, and bulk import from CSV with row-by-row validation.
- **Approval workflow:** owners ask for a product to go live, and an admin approves or rejects the request.
- **Timed auctions:** an approved product is open for bidding for 1 hour. Every bid must beat the current price, and owners can't bid on their own products.
- **Automatic closing:** a Celery beat task closes expired auctions every 10 seconds.
- **Email notifications:** owners and highest bidders are emailed when an auction closes, and winners when their bid is accepted or rejected. Emails go through an outbox table, so none are lost if SMTP is down.
- **Concurrency safety:** bids, approvals and status changes lock rows (`SELECT ... FOR UPDATE`), so two simultaneous requests can't corrupt an auction.

## Auction lifecycle

```
draft ──(owner requests, admin approves)──▶ active ──(1 hour passes)──▶ closed ──(owner decides)──▶ sold / rejected
```

## Tech stack

| Area | Tools |
| --- | --- |
| API | FastAPI, Pydantic v2 |
| Database | PostgreSQL, SQLAlchemy 2 |
| Auth | python-jose (JWT), passlib/bcrypt |
| Background jobs | Celery with Redis (worker and beat) |
| Email | SMTP |
| Tests | pytest, httpx, pytest-cov |
| Tooling | uv, Python 3.12+ |

## Getting started

### 1. Requirements

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis, running on `localhost:6379`
- An SMTP account for sending emails (Gmail with an app password works)

### 2. Install

```bash
git clone https://github.com/Mus1eh/auctionAPI.git
cd auctionAPI
uv sync
```

### 3. Configure

```bash
cp .env.example .env
```

Fill in `.env`:

| Variable | Purpose |
| --- | --- |
| `SQLALCHEMY_URL` | Main database, for example `postgresql://user:pass@localhost:5432/auctionapi` |
| `SQLALCHEMY_TEST_URL` | Separate database used only by the tests. Its name must be `auctionapi_test` |
| `SECRET_KEY`, `ALGORITHM` | JWT signing, for example a long random string and `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `RESET_PASSWORD_TOKEN_EXPIRE_MINUTES` | Token lifetimes |
| `SUPERADMIN_*`, `ADMIN_*` | Accounts created by the seed script |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` | Outgoing email |
| `FRONTEND_URL` | Base of the password reset link: `{FRONTEND_URL}/reset-password?token=...` |

### 4. Create the tables and seed data

There are no migrations yet, so create the tables once with:

```bash
uv run python -c "from app import models; from app.database import Base, engine; Base.metadata.create_all(engine)"
```

Then create the roles plus the superadmin and admin accounts, and optionally some sample products:

```bash
uv run python -m app.seeders.seeds
uv run python -m app.seeders.products_seed
```

### 5. Run

You need three terminals:

```bash
# API, at http://localhost:8000
uv run uvicorn app.main:app --reload

# Celery worker, which runs the background tasks
uv run celery -A app.celery_app worker --loglevel=info

# Celery beat, which closes expired auctions and sends queued emails every 10 seconds
uv run celery -A app.celery_app beat --loglevel=info
```

Interactive API docs are at **http://localhost:8000/docs**.

## API overview

Endpoints marked 🔒 need an `Authorization: Bearer <access_token>` header.

### Auth: `/auth`
| Method | Path | Description |
| --- | --- | --- |
| POST | `/auth/` | Log in. Form data with `username` (or email) and `password`. Returns access and refresh tokens |
| POST | `/auth/refresh` | Swap a refresh token for a new token pair. The old refresh token is revoked |
| POST | `/auth/logout` | Revoke a refresh token |
| POST | `/auth/logout-all` 🔒 | Revoke all of the user's sessions |
| POST | `/auth/change-password` 🔒 | Change password |
| POST | `/auth/forgot-password` | Email a reset link |
| POST | `/auth/verify-token` | Check that a reset token is valid |
| POST | `/auth/reset-password` | Set a new password with a reset token |

### Users: `/users`
| Method | Path | Description |
| --- | --- | --- |
| POST | `/users/` | Sign up |
| GET | `/users/{id}` 🔒 | Get a user (admin only) |
| DELETE | `/users/{id}` 🔒 | Delete your own account, or any regular user's as an admin |

### Products: `/products`
| Method | Path | Description |
| --- | --- | --- |
| POST | `/products/` 🔒 | Create a product (starts as `draft`) |
| POST | `/products/import-csv` 🔒 | Bulk create from a CSV with `name,description,start_price` columns (max 2 MB) |
| GET | `/products/my` 🔒 | List your products |
| GET | `/products/status/{status}` | List products by status |
| GET | `/products/{id}` | Get a product |
| PUT / PATCH | `/products/{id}` 🔒 | Update a product, fully or partially (owner or admin) |
| DELETE | `/products/{id}` 🔒 | Delete a product (owner or admin) |
| POST | `/products/{id}/status-request?request=active` 🔒 | Ask an admin to start the auction |

### Bids: `/bids`
| Method | Path | Description |
| --- | --- | --- |
| POST | `/bids/{product_id}` 🔒 | Place a bid, with `{ "amount": 150 }` |
| GET | `/bids/{product_id}?page=1&limit=20` | Bid history, newest first |
| POST | `/bids/{product_id}/approve?request=approve\|reject` 🔒 | Owner accepts or rejects the highest bid after the auction closes |

### Admin: `/admin` 🔒 (admin or superadmin)
| Method | Path | Description |
| --- | --- | --- |
| GET | `/admin/dashboard` | Returns the current user's username and role |
| GET | `/admin/status-request/pending` | List pending go-live requests |
| PATCH | `/admin/status-requests/{id}/approve` | Approve a request, which starts the 1-hour auction |
| PATCH | `/admin/status-requests/{id}/reject` | Reject a request |
| POST | `/admin/products/{id}/status/{active\|closed}` | Start or close an auction directly |
| PATCH | `/admin/users/{id}/role` | Set a user's role to `user` or `admin` (superadmin only) |

## Running the tests

The tests need their own PostgreSQL database named `auctionapi_test`, set in `SQLALCHEMY_TEST_URL`. Never point it at real data.

```bash
uv run pytest -v tests --ignore=tests/test_concurrency.py
uv run pytest -v tests/test_concurrency.py   # run this one on its own
```

Add coverage with `--cov=app --cov-report=html`. The report goes to `htmlcov/`. See [tests/README.md](tests/README.md) for details.

## Project structure

```
app/
  main.py              FastAPI app and router registration
  models.py            SQLAlchemy models
  schemas.py           Pydantic request and response models
  enums.py             Product, bid and approval statuses
  database.py          Engine and session
  oauth2.py            JWT access tokens and the current user
  refresh_token.py     Refresh token storage and rotation
  password_reset.py    Reset token handling
  permissions.py       Role and ownership checks
  routers/             auth, users, products, bids, admin
  services/            Auction closing logic
  celery_app.py        Celery config and beat schedule
  tasks.py             Background tasks: close auctions, send emails from the outbox
  email_service.py     SMTP sending
  email_templates.py   Email bodies
  seeders/             Seed scripts for roles, admins and sample products
tests/                 pytest suite
frontend/              React frontend (main branch only, see frontend/README.md)
```

## Notes

- **CORS:** CORS isn't configured. A frontend on another origin needs either a dev proxy (the included frontend uses one) or `CORSMiddleware` added in `app/main.py`.
- **Empty lists:** `GET /products/my` and `GET /products/status/{status}` return `404` instead of an empty list when nothing matches.
- **Live prices:** there's no WebSocket support. Clients get live prices by polling `GET /products/{id}`.
