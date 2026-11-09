from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError

from app.core.config import settings
from app.core.exceptions import AppError
from app.routers import admin, authentication, bids, product, user

is_dev = settings.environment == "development"

app = FastAPI(
    title="Auction API",
    description="An API for managing auctions",
    version="2.4.2",
    docs_url="/docs" if is_dev else None,
    redoc_url="/redoc" if is_dev else None,
    openapi_url="/openapi.json" if is_dev else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)

app.include_router(admin.router)
app.include_router(authentication.router)
app.include_router(bids.router)
app.include_router(user.router)
app.include_router(product.router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "The request contains a value that cannot be stored."},
    )


DOCS_PATHS = {"/docs", "/redoc", "/docs/oauth2-redirect"}
DOCS_CSP = (
    "default-src 'none'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net "
    "https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com "
    "https://cdn.redoc.ly; "
    "worker-src blob:; "
    "connect-src 'self'; frame-ancestors 'none'"
)
API_CSP = "default-src 'none'; frame-ancestors 'none'"


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        DOCS_CSP if request.url.path in DOCS_PATHS else API_CSP
    )
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    return response
