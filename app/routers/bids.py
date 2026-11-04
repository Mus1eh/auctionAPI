from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import get_bid_repo, get_product_repo
from app.enums import ApproveBidding
from app.oauth2 import get_current_user, get_current_user_optional
from app.repositories.bids import BidRepository
from app.repositories.product import ProductRepository
from app.services.bids.approvebid import approve_bid as approve_bid_service
from app.services.bids.create import create_bid as create_bid_service
from app.services.bids.get import get_bids_for_product as get_bids_for_product_service

router = APIRouter(prefix="/bids", tags=["Bids"])


@router.post(
    "/{product_id}", response_model=schemas.BidShow, status_code=status.HTTP_201_CREATED
)
def create_bid(
    product_id: int,
    request: schemas.BidCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    product_repo: ProductRepository = Depends(get_product_repo),
    bid_repo: BidRepository = Depends(get_bid_repo),
):
    return create_bid_service(
        product_id=product_id,
        db=db,
        request=request,
        current_user=current_user,
        bid_repo=bid_repo,
        product_repo=product_repo,
    )


@router.get(
    "/{product_id}",
    response_model=list[schemas.BidShow],
)
def get_bids_for_product(
    product_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=20),
    current_user: models.User | None = Depends(get_current_user_optional),
    product_repo: ProductRepository = Depends(get_product_repo),
    bid_repo: BidRepository = Depends(get_bid_repo),
):
    return get_bids_for_product_service(
        product_id=product_id,
        page=page,
        limit=limit,
        product_repo=product_repo,
        bid_repo=bid_repo,
        current_user=current_user,
    )


@router.post(
    "/{product_id}/approve",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ProductApprovalShow,
)
def approve_bid(
    product_id: int,
    request: ApproveBidding,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    bid_repo: BidRepository = Depends(get_bid_repo),
    product_repo: ProductRepository = Depends(get_product_repo),
):
    return approve_bid_service(
        db=db,
        product_id=product_id,
        request=request,
        current_user=current_user,
        bid_repo=bid_repo,
        product_repo=product_repo,
    )


# async function refreshAuction(productId) {
#     const response = await fetch(`/products/${productId}`);
#     const product = await response.json();

#     document.getElementById("current-price").textContent =
#         product.current_price;
# }

# setInterval(() => {
#     refreshAuction(10);
# }, 2000);

# use the above code in frontend, it's called HTTP Polling -> refresh data every 2 seconds to get latest data.
