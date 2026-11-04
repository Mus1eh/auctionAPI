from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.enums import ProductStatus
from app.repositories.email_outbox import EmailOutboxRepository
from app.repositories.product import ProductRepository
from app.services.auctions.close import close_auction


def change_product_status(
    db: Session,
    product_repo: ProductRepository,
    product_id: int,
    status_value: ProductStatus,
    outbox_repo: EmailOutboxRepository,
):
    try:
        product = product_repo.get_by_id_for_update(product_id)

        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found.",
            )

        if product.status == status_value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The requested status is the same as the current status.",
            )

        if status_value == ProductStatus.CLOSED:
            if product.status != ProductStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only active auctions can be closed.",
                )

            close_auction(db, product, outbox_repo)

        elif status_value == ProductStatus.ACTIVE:
            if product.status != ProductStatus.DRAFT:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Only draft products can be activated.",
                )

            now = datetime.now(UTC)

            product_repo.update(
                product,
                {
                    "status": ProductStatus.ACTIVE,
                    "auction_started_at": now,
                    "auction_ends_at": now + timedelta(hours=1),
                },
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint supports activating or closing auctions only.",
            )

        db.commit()
        db.refresh(product)

        return product

    except Exception:
        db.rollback()
        raise
