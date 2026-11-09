from typing import Annotated

from pydantic import AfterValidator, StringConstraints

from app.core.limits import PRODUCT_DESCRIPTION_MAX, PRODUCT_NAME_MAX


def reject_html(value: str) -> str:
    if "<" in value or ">" in value:
        raise ValueError("HTML tags are not allowed.")

    return value


# Whitespace is stripped before the length checks, so "   " fails min_length.
# Optional fields use `ProductDescription | None`; None skips these checks.
ProductName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=1, max_length=PRODUCT_NAME_MAX
    ),
    AfterValidator(reject_html),
]

ProductDescription = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=PRODUCT_DESCRIPTION_MAX),
    AfterValidator(reject_html),
]
