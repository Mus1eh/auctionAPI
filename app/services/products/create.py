from sqlalchemy.orm import Session

from app import models, schemas
from app.repositories.product import ProductRepository


def create_product(
    db: Session,
    repo: ProductRepository,
    request: schemas.ProductCreate,
    current_user: models.User,
):
    new_product = models.Product(
        **request.model_dump(),
        owner_id=current_user.id,
        current_price=request.start_price,
    )

    try:
        product = repo.create(new_product)
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise
