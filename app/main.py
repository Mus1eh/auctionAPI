from fastapi import FastAPI

from app.database import Base, engine
from app.routers import admin, authentication, bids, product, user

app = FastAPI(
    title="PROJECT ManAPI",
)

Base.metadata.create_all(bind=engine)

app.include_router(bids.router)
app.include_router(admin.router)
app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(product.router)
