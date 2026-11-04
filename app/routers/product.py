from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_product_repo, get_product_status_request_repo
from app.enums import ProductStatus
from app.oauth2 import get_current_user, get_current_user_optional
from app.repositories.product import ProductRepository
from app.repositories.product_status_request import ProductStatusRequestRepository
from app.services.products.create import create_product as create_product_service
from app.services.products.csv import (
    import_products_csv as import_products_csv_service,
)
from app.services.products.delete import delete_product as delete_product_service
from app.services.products.get import get_by_status as get_by_status_service
from app.services.products.get import get_my_product as get_my_product_service
from app.services.products.get import get_product as get_product_service
from app.services.products.restore_draft import restore_draft as restore_draft_service
from app.services.products.status_change import (
    request_status_change as request_status_change_service,
)
from app.services.products.update import update_product as update_product_service

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

# ONLY THE OWNER CAN SEE THESE (ADMINS SEE EVERYONE'S FROM THE ADMIN DASHBOARD)
PRIVATE_STATUSES = (ProductStatus.DRAFT, ProductStatus.REJECTED)

EDITABLE_STATUSES = (ProductStatus.DRAFT, ProductStatus.REJECTED)

CLIENT_EDITABLE_FIELDS = ("name", "description", "start_price")


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
    repo: ProductRepository = Depends(get_product_repo),
):
    return create_product_service(
        db=db,
        repo=repo,
        request=request,
        current_user=current_user,
    )


# GET MY PRODUCTS
@router.get(
    "/my", response_model=list[schemas.ProductShow], response_model_exclude_none=True
)
def get_my_products(
    current_user: models.User = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repo),
):
    return get_my_product_service(
        repo=repo,
        current_user=current_user,
    )


# GET ALL PRODUCTS BY STATUS IT'S BETTER THAN TO GET ALL PRODUCTS AT ONCE SO THE DATABASE CAN HANDLE
# AND FRONT END CAN HANDLE IT BETTER AND ALSO WE CAN ADD PAGINATION LATER ON
@router.get(
    "/status/{stat}",
    response_model=list[schemas.ProductShow],
    response_model_exclude_none=True,
)
def get_products(
    stat: ProductStatus,
    current_user: models.User | None = Depends(get_current_user_optional),
    repo: ProductRepository = Depends(get_product_repo),
):
    return get_by_status_service(
        repo=repo,
        product_status=stat,
        current_user=current_user,
    )


# GET PRODUCT BY ID
@router.get(
    "/{id}", response_model=schemas.ProductShow, response_model_exclude_none=True
)
def get_product(
    id: int,
    current_user: models.User | None = Depends(get_current_user_optional),
    repo: ProductRepository = Depends(get_product_repo),
):
    return get_product_service(
        repo=repo,
        product_id=id,
        current_user=current_user,
    )


# UPDATE ENTIRE PRODUCT
@router.put(
    "/{id}",
    response_model=schemas.ProductShow,
    response_model_exclude_none=True,
)
def update_product(
    id: int,
    request: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repo),
):
    return update_product_service(
        db=db,
        repo=repo,
        product_id=id,
        request=request.model_dump(),
        current_user=current_user,
    )


# PARTIAL UPDATE PRODUCT
@router.patch("/{id}", response_model=schemas.ProductShow)
def patch_product(
    id: int,
    request: schemas.ProductPatch,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repo),
):
    return update_product_service(
        db=db,
        repo=repo,
        product_id=id,
        request=request.model_dump(exclude_unset=True),
        current_user=current_user,
    )


# DELETE PRODUCT
@router.delete("/{id}", status_code=status.HTTP_202_ACCEPTED)
def delete_product(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return delete_product_service(
        db=db,
        repo=repo,
        product_id=id,
        current_user=current_user,
        status_repo=status_repo,
    )


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
    repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return request_status_change_service(
        db=db,
        repo=repo,
        status_repo=status_repo,
        product_id=id,
        request=request,
        current_user=current_user,
    )


@router.post("/{id}/restore-draft", response_model=schemas.ProductShow)
def restore_product_to_draft(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repo),
    status_repo: ProductStatusRequestRepository = Depends(
        get_product_status_request_repo
    ),
):
    return restore_draft_service(
        db=db,
        repo=repo,
        status_repo=status_repo,
        product_id=id,
        current_user=current_user,
    )

    # CREATE UNIQUE INDEX uq_product_pending_status_request
    # ON product_status_requests (product_id) ----------------------> THIS ASUURES THAT NO MORE THAN ONE PENDING REQUEST EXISTS FOR A SINGLE RODUCT
    # WHERE approval_status = 'pending'; -----> ALSO WE HAVE THE 409 CONFLICT SO WE GOT 2 LAYERS OF PROTECTION AGAINST MULTIPLE PENDING REQUESTS


@router.post("/import-csv", status_code=status.HTTP_201_CREATED)
def import_products_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    repo: ProductRepository = Depends(get_product_repo),
):
    return import_products_csv_service(
        db=db,
        repo=repo,
        file=file,
        current_user=current_user,
    )
