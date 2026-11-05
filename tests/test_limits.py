"""Input limits: too big is refused by validation, exactly at the limit works, and the
schemas never allow more than the database columns hold."""

import pytest

from app import models, schemas
from app.core import limits
from app.enums import ProductStatus

NAME = limits.PRODUCT_NAME_MAX
DESCRIPTION = limits.PRODUCT_DESCRIPTION_MAX
INT_MAX = limits.INT_MAX

DATABASE_FALLBACK = "The request contains a value that cannot be stored."


def refused(response) -> bool:
    """Rejected by request validation, not caught late by the database fallback."""
    return (
        response.status_code == 422 and response.json()["detail"] != DATABASE_FALLBACK
    )


def email_of(length: int) -> str:
    """A valid address of exactly `length` characters (64-character local part)."""
    return f"{'a' * 64}@{'b' * (length - 64 - 1 - 4)}.com"


# --- product fields: create, replace, patch ---------------------------------

PRODUCT_FIELDS = [
    ("name", "a" * NAME, "a" * (NAME + 1)),
    ("description", "d" * DESCRIPTION, "d" * (DESCRIPTION + 1)),
    ("start_price", INT_MAX, INT_MAX + 1),
]


@pytest.mark.parametrize(("field", "at_limit", "too_big"), PRODUCT_FIELDS)
def test_creating_a_product_enforces_the_limit(
    client, make_user, auth, field, at_limit, too_big
):
    headers = auth(make_user())
    body = {"name": "n", "start_price": 10}

    over = client.post("/products/", json={**body, field: too_big}, headers=headers)
    at = client.post("/products/", json={**body, field: at_limit}, headers=headers)

    assert refused(over)
    assert at.status_code == 201


@pytest.mark.parametrize(("field", "at_limit", "too_big"), PRODUCT_FIELDS)
def test_replacing_a_product_enforces_the_limit(
    client, make_user, make_product, auth, field, at_limit, too_big
):
    owner = make_user()
    product = make_product(owner)
    url, headers = f"/products/{product.id}", auth(owner)
    body = {"name": "n", "start_price": 10}

    over = client.put(url, json={**body, field: too_big}, headers=headers)
    at = client.put(url, json={**body, field: at_limit}, headers=headers)

    assert refused(over)
    assert at.status_code == 200


@pytest.mark.parametrize(("field", "at_limit", "too_big"), PRODUCT_FIELDS)
def test_patching_a_product_enforces_the_limit(
    client, make_user, make_product, auth, field, at_limit, too_big
):
    owner = make_user()
    product = make_product(owner)
    url, headers = f"/products/{product.id}", auth(owner)

    over = client.patch(url, json={field: too_big}, headers=headers)
    at = client.patch(url, json={field: at_limit}, headers=headers)

    assert refused(over)
    assert at.status_code == 200


def test_an_empty_product_name_is_refused(client, make_user, auth):
    response = client.post(
        "/products/", json={"name": "", "start_price": 10}, headers=auth(make_user())
    )
    assert refused(response)


# --- csv import ---------------------------------------------------------------


def import_csv(client, headers, row: str):
    content = f"name,description,start_price\n{row}\n".encode()
    return client.post(
        "/products/import-csv",
        files={"file": ("products.csv", content, "text/csv")},
        headers=headers,
    )


@pytest.mark.parametrize(
    "row",
    [
        f"A,{'d' * (DESCRIPTION + 1)},5",
        f"{'a' * (NAME + 1)},d,5",
        f"A,d,{INT_MAX + 1}",
    ],
)
def test_csv_rows_over_the_limit_are_refused(client, make_user, auth, row):
    assert refused(import_csv(client, auth(make_user()), row))


@pytest.mark.parametrize(
    "row",
    [f"A,{'d' * DESCRIPTION},5", f"{'a' * NAME},d,5", f"A,d,{INT_MAX}"],
)
def test_csv_rows_at_the_limit_are_imported(client, make_user, auth, row):
    assert import_csv(client, auth(make_user()), row).status_code == 201


# --- bids ----------------------------------------------------------------------


def test_a_bid_amount_cannot_exceed_the_integer_column(
    client, make_user, make_product, auth
):
    product = make_product(make_user(), ProductStatus.ACTIVE)
    headers = auth(make_user())
    url = f"/bids/{product.id}"

    over = client.post(url, json={"amount": INT_MAX + 1}, headers=headers)
    at = client.post(url, json={"amount": INT_MAX}, headers=headers)

    assert refused(over)
    assert at.status_code == 201


# --- users and passwords ---------------------------------------------------------


def register(client, name: str, email: str, password: str = "StrongPass123!"):
    return client.post(
        "/users/", json={"username": name, "email": email, "password": password}
    )


def test_username_length_limits(client, roles):
    assert refused(register(client, "ab", "short@example.com"))
    assert register(client, "abc", "min@example.com").status_code == 201
    at_max = register(client, "u" * limits.USERNAME_MAX, "max@example.com")
    over = register(client, "u" * (limits.USERNAME_MAX + 1), "over@example.com")
    assert at_max.status_code == 201
    assert refused(over)


def test_email_length_limit(client, roles):
    at = register(client, "emailmax", email_of(limits.EMAIL_MAX))
    over = register(client, "emailover", email_of(limits.EMAIL_MAX + 1))
    assert at.status_code == 201
    assert refused(over)


def test_password_length_limits(client, roles):
    too_short = register(
        client, "pwshort", "pwshort@example.com", "p" * (limits.PASSWORD_MIN - 1)
    )
    at = register(client, "pwmax", "pwmax@example.com", "p" * limits.PASSWORD_MAX)
    over = register(
        client, "pwover", "pwover@example.com", "p" * (limits.PASSWORD_MAX + 1)
    )
    assert refused(too_short)
    assert at.status_code == 201
    assert refused(over)


def test_a_new_password_cannot_be_longer_than_the_limit_anywhere(
    client, make_user, auth
):
    too_long = "n" * (limits.PASSWORD_MAX + 1)

    change = client.post(
        "/auth/change-password",
        json={"current_password": "TestPassword123!", "new_password": too_long},
        headers=auth(make_user()),
    )
    reset = client.post(
        "/auth/reset-password", json={"token": "x", "new_password": too_long}
    )
    forgot = client.post(
        "/auth/forgot-password", json={"email": email_of(limits.EMAIL_MAX + 1)}
    )

    assert refused(change)
    assert refused(reset)
    assert refused(forgot)


# --- the schemas and the database columns must agree -------------------------------


def schema_property(model, field: str) -> dict:
    prop = model.model_json_schema()["properties"][field]
    if "anyOf" in prop:
        prop = next(p for p in prop["anyOf"] if p.get("type") != "null")
    return prop


@pytest.mark.parametrize(
    ("column", "limit"),
    [
        (models.Product.__table__.c.name, limits.PRODUCT_NAME_MAX),
        (models.Product.__table__.c.description, limits.PRODUCT_DESCRIPTION_MAX),
        (models.User.__table__.c.username, limits.USERNAME_MAX),
        (models.User.__table__.c.email, limits.EMAIL_MAX),
    ],
)
def test_database_columns_use_the_shared_limits(column, limit):
    assert column.type.length == limit


@pytest.mark.parametrize(
    ("model", "field", "keyword", "limit"),
    [
        (schemas.ProductCreate, "name", "maxLength", limits.PRODUCT_NAME_MAX),
        (
            schemas.ProductCreate,
            "description",
            "maxLength",
            limits.PRODUCT_DESCRIPTION_MAX,
        ),
        (schemas.ProductCreate, "start_price", "maximum", limits.INT_MAX),
        (schemas.ProductPatch, "name", "maxLength", limits.PRODUCT_NAME_MAX),
        (
            schemas.ProductPatch,
            "description",
            "maxLength",
            limits.PRODUCT_DESCRIPTION_MAX,
        ),
        (schemas.ProductPatch, "start_price", "maximum", limits.INT_MAX),
        (schemas.ProductCSVImport, "name", "maxLength", limits.PRODUCT_NAME_MAX),
        (
            schemas.ProductCSVImport,
            "description",
            "maxLength",
            limits.PRODUCT_DESCRIPTION_MAX,
        ),
        (schemas.ProductCSVImport, "start_price", "maximum", limits.INT_MAX),
        (schemas.BidCreate, "amount", "maximum", limits.INT_MAX),
        (schemas.UserCreate, "username", "maxLength", limits.USERNAME_MAX),
        (schemas.UserCreate, "username", "minLength", limits.USERNAME_MIN),
        (schemas.UserCreate, "email", "maxLength", limits.EMAIL_MAX),
        (schemas.UserCreate, "password", "maxLength", limits.PASSWORD_MAX),
        (schemas.UserCreate, "password", "minLength", limits.PASSWORD_MIN),
        (schemas.ForgotPasswordRequest, "email", "maxLength", limits.EMAIL_MAX),
        (
            schemas.ResetPasswordRequest,
            "new_password",
            "maxLength",
            limits.PASSWORD_MAX,
        ),
        (
            schemas.ChangePasswordRequest,
            "new_password",
            "maxLength",
            limits.PASSWORD_MAX,
        ),
    ],
)
def test_schemas_use_the_shared_limits(model, field, keyword, limit):
    assert schema_property(model, field)[keyword] == limit
