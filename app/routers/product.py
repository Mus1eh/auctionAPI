from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.oauth2 import get_current_user
from app.permissions import require_product_owner_or_admin

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# CREATE PRODUCT
@router.post(
    "/", response_model=schemas.ProductShow, status_code=status.HTTP_201_CREATED
)
def create_product(
    request: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_product = models.Product(**request.model_dump(), owner_id=current_user.id)
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# GET MY PRODUCTS
@router.get("/my", response_model=list[schemas.ProductShow])
def get_my_products(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    products = (
        db.query(models.Product)
        .filter(models.Product.owner_id == current_user.id)
        .all()
    )
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="You have no products."
        )
    return products


# GET ALL PRODUCTS
@router.get("/", response_model=list[schemas.ProductShow])
def get_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No products found."
        )
    return products


# GET PRODUCT BY ID
@router.get("/{id}", response_model=schemas.ProductShow)
def get_product(id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found."
        )
    return product


# UPDATE ENTIRE PRODUCT
@router.put("/{id}", response_model=schemas.ProductShow)
def update_product(
    id: int,
    request: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found."
        )
    require_product_owner_or_admin(product, current_user)

    for key, value in request.model_dump().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


# PARTIAL UPDATE PRODUCT
@router.patch("/{id}", response_model=schemas.ProductShow)
def patch_product(
    id: int,
    request: schemas.ProductPatch,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found."
        )
    require_product_owner_or_admin(product, current_user)

    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product


# DELETE PRODUCT
@router.delete("/{id}", status_code=status.HTTP_202_ACCEPTED)
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(
            stauts_code=status.HTTP_404_NOT_FOUND, detail="Product is not found."
        )
    require_product_owner_or_admin(product, current_user)
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted successfully."}
