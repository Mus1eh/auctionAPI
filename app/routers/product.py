import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.enums import ApprovalStatus, ProductStatus
from app.oauth2 import get_current_user
from app.permissions import require_product_owner_or_admin

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


# CREATE PRODUCT
@router.post(
    "/",
    response_model=schemas.ProductShow,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
)
def create_product(
    request: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    new_product = models.Product(
        **request.model_dump(),
        owner_id=current_user.id,
        current_price=request.start_price,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# GET MY PRODUCTS
@router.get(
    "/my", response_model=list[schemas.ProductShow], response_model_exclude_none=True
)
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


# GET ALL PRODUCTS BY STATUS IT'S BETTER THAN TO GET ALL PRODUCTS AT ONCE SO THE DATABASE CAN HANDLE
# AND FRONT END CAN HANDLE IT BETTER AND ALSO WE CAN ADD PAGINATION LATER ON
@router.get(
    "/status/{stat}",
    response_model=list[schemas.ProductShow],
    response_model_exclude_none=True,
)
def get_products(stat: ProductStatus, db: Session = Depends(get_db)):
    products = db.query(models.Product).filter(models.Product.status == stat).all()
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No products found."
        )
    return products


@router.post("/import-csv", status_code=status.HTTP_201_CREATED)
def import_products_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only csv files can be imported.",
        )

    try:
        content = file.file.read(2 * 1024 * 1024 + 1)

        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="CSV file exceeds the 2 MB size limit.",
            )

        decoded_content = content.decode("utf-8")

        reader = csv.DictReader(io.StringIO(decoded_content))

        expected_columns = {"name", "description", "start_price"}

        if (
            reader.fieldnames is None
            or len(reader.fieldnames) != len(expected_columns)
            or set(reader.fieldnames) != expected_columns
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must contain name, description and start_price columns.",
            )

        products = []
        errors = []

        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError("Invalid CSV column count")

                validated = schemas.ProductCSVImport.model_validate(row)

                products.append(
                    models.Product(
                        name=validated.name,
                        description=validated.description,
                        start_price=validated.start_price,
                        current_price=validated.start_price,
                        owner_id=current_user.id,
                        status=ProductStatus.DRAFT,
                    )
                )

            except (ValidationError, ValueError) as exc:
                errors.append(
                    {
                        "row": row_number,
                        "error": str(
                            exc,
                        ),
                    }
                )

        if errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": "CSV validation failed, No products were imported.",
                    "errors": errors,
                },
            )

        if not products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV contain no product",
            )

        db.add_all(products)
        db.commit()

        return {
            "message": "Products imported successfully.",
            "imported_count": len(products),
        }
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must be UTF-8 encoded.",
        )

    except Exception:
        db.rollback()
        raise

    finally:
        file.file.close()


# GET PRODUCT BY ID
@router.get(
    "/{id}", response_model=schemas.ProductShow, response_model_exclude_none=True
)
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found."
        )
    require_product_owner_or_admin(product, current_user)
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted successfully."}


@router.post(
    "/{id}/status-request",
    response_model=schemas.ProductStatusRequestShow,
    status_code=status.HTTP_201_CREATED,
)
def request_status_change(
    id: int,
    request: ProductStatus,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product is not found."
        )

    if product.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this product.",
        )
    pending_request = (
        db.query(models.ProductStatusRequest)
        .filter(
            models.ProductStatusRequest.product_id == product.id,
            models.ProductStatusRequest.approval_status == ApprovalStatus.PENDING,
        )
        .first()
    )

    if pending_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There is already a pending request for this product.",
        )

    allowed_transitions = {
        ProductStatus.DRAFT: {ProductStatus.ACTIVE},
    }

    if request == product.status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The requested status is the same as the current status.",
        )

    if request == ProductStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot request to close the product, please wait until the timer runs out.",
        )

    if request not in allowed_transitions.get(product.status, set()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product status transition.",
        )

    new_request = models.ProductStatusRequest(
        product_id=product.id,
        requested_status=request,
        approval_status=ApprovalStatus.PENDING,
        requested_by=current_user.id,
    )

    try:
        db.add(new_request)
        db.commit()
        db.refresh(new_request)

    except Exception:
        db.rollback()
        raise

    return new_request

    # CREATE UNIQUE INDEX uq_product_pending_status_request
    # ON product_status_requests (product_id) ----------------------> THIS ASUURES THAT NO MORE THAN ONE PENDING REQUEST EXISTS FOR A SINGLE RODUCT
    # WHERE approval_status = 'pending'; -----> ALSO WE HAVE THE 409 CONFLICT SO WE GOT 2 LAYERS OF PROTECTION AGAINST MULTIPLE PENDING REQUESTS
