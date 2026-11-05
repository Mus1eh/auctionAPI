from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError

from app.core.exceptions import AppError
from app.routers import admin, authentication, bids, product, user

app = FastAPI(
    title="PROJECT ManAPI",
)

app.include_router(bids.router)
app.include_router(admin.router)
app.include_router(authentication.router)
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
