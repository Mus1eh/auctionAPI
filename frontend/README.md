# Lotwise — frontend for the FastAPI Auction API

React 19 + TypeScript + Vite, Tailwind CSS v4, React Router 7, TanStack Query 5, React Hook Form + Zod, Lucide icons.
Tested with Vitest + Testing Library (mocked API) and Playwright (live backend).

## Setup

```bash
cd frontend
npm install
cp .env.example .env        # defaults work for local development
npm run dev                 # http://localhost:5173 (backend expected on http://localhost:8000)
```

| Variable | Where | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | browser | API base URL. Default `/api` goes through the Vite proxy. |
| `API_PROXY_TARGET` | dev server only | Where `/api` is proxied (default `http://localhost:8000`). |
| `VITE_CURRENCY` | browser | Optional ISO code for price display; the API stores plain integers. |

**CORS:** the backend has no `CORSMiddleware`. In development the Vite proxy makes requests same-origin, so no backend change is needed.
If you deploy the built app on a different origin than the API, either reverse-proxy `/api` to FastAPI or add
`CORSMiddleware(allow_origins=[<frontend origin>], allow_methods=["*"], allow_headers=["Authorization", "Content-Type"])`.

**Password reset links** are built from the backend's `FRONTEND_URL` as `{FRONTEND_URL}/reset-password?token=…`.
Set `FRONTEND_URL=http://localhost:5173` in the backend `.env` (it currently points to `:8000`, the API itself).

## Scripts

```bash
npm run typecheck   # tsc
npm run lint        # eslint
npm test            # vitest (unit + component, API mocked)
npm run build       # production build to dist/
npm run test:e2e    # playwright against a running frontend + backend (see below)
npm run gen:api     # regenerate src/api/schema.d.ts from the running backend's /openapi.json
```

### End-to-end tests (live backend)

The suite registers users, creates listings, bids, and needs a **superadmin** account. Point it at a disposable database
(never production). Credentials go in the gitignored `frontend/.env.e2e.local`:

```
E2E_BASE_URL=http://localhost:5174
E2E_SUPERADMIN_USERNAME=...
E2E_SUPERADMIN_PASSWORD=...
```

Example using the test database:

```bash
# terminal 1 (repo root)
SQLALCHEMY_URL="<SQLALCHEMY_TEST_URL value>" uv run uvicorn app.main:app --port 8001
# terminal 2 (frontend/)
API_PROXY_TARGET=http://localhost:8001 npx vite --port 5174
# terminal 3 (frontend/)
npx playwright install chromium   # first time only
npm run test:e2e
```

## Structure

```
src/
  api/          client (fetch, errors, token refresh), endpoints, TanStack Query hooks, generated OpenAPI types
  auth/         AuthProvider, session restore, route guards (UX only — the backend enforces permissions)
  components/   ui/ primitives, layout/, product/ (cards, bid panel, bid history, seller & admin actions, CSV import)
  pages/        marketplace, product detail, sell/edit, my listings, account, auth/, admin/
  lib/          formatting, zod schemas, client-side search/sort
e2e/            Playwright specs
```

## How it maps to the API

- **Auth:** OAuth2 password form to `POST /auth/`. The access token is kept in memory only. The refresh token is stored in
  `localStorage` so sessions survive a reload. On a 401 the client refreshes once (single-flight, because the backend
  rotates refresh tokens) and retries the request. Logout revokes the refresh token on the server.
- **Who am I:** there is no `/me` endpoint. The username comes from the JWT `sub` claim, and the role from probing
  `GET /admin/dashboard` (200 means admin/superadmin, 403 means user). Ownership comes from `GET /products/my`.
- **Listings:** the API only lists products by status (`/products/status/{status}`). Search and sort happen client-side.
  Live auctions are polled every 5s, since the API has no push channel.

## Known API limitations

- No product images, categories, server-side search or pagination for products. Covers are generated from the name.
- No user directory and no usernames for bidders/sellers, so the UI shows `Bidder #id` / `Seller #id`. Admins look up users by ID.
- Users can't see their own go-live requests (only admins can list pending ones), and can't find their own user id
  unless they own a product.
- **Backend bug:** `GET /products/status/{status}` returns **500** instead of 404 when no product has that status.
  The `status` path parameter shadows `fastapi.status`, so `status.HTTP_404_NOT_FOUND` raises an AttributeError
  (`app/routers/product.py`, `get_products`). The UI shows an error state for empty tabs until this is fixed
  (e.g. `from fastapi import status as http_status`, or rename the parameter).
