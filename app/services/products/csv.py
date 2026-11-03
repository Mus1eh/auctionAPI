import csv
import io

from fastapi import HTTPException, UploadFile, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import models, schemas
from app.enums import ProductStatus
from app.repositories.product import ProductRepository


def import_products_csv(
    db: Session, file: UploadFile, repo: ProductRepository, current_user: models.User
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
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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

        repo.create_bulk(products)
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
