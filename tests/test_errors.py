import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core import exceptions
from app.main import app_error_handler


def make_client(error: exceptions.AppError) -> TestClient:
    test_app = FastAPI()
    test_app.add_exception_handler(exceptions.AppError, app_error_handler)

    @test_app.get("/boom")
    def boom():
        raise error

    return TestClient(test_app)


@pytest.mark.parametrize(
    ("error_class", "status_code"),
    [
        (exceptions.BadRequestError, 400),
        (exceptions.UnauthorizedError, 401),
        (exceptions.ForbiddenError, 403),
        (exceptions.NotFoundError, 404),
        (exceptions.ConflictError, 409),
        (exceptions.PayloadTooLargeError, 413),
        (exceptions.UnprocessableError, 422),
    ],
)
def test_categories_map_to_their_status_code(error_class, status_code):
    response = make_client(error_class("Something went wrong.")).get("/boom")
    assert response.status_code == status_code
    assert response.json() == {"detail": "Something went wrong."}
    assert "www-authenticate" not in response.headers


def test_structured_detail_is_returned_unchanged():
    detail = {"message": "Validation failed.", "errors": [{"row": 2, "error": "bad"}]}
    response = make_client(exceptions.UnprocessableError(detail)).get("/boom")
    assert response.status_code == 422
    assert response.json() == {"detail": detail}


def test_headers_are_sent():
    error = exceptions.UnauthorizedError(
        "Invalid refresh token", headers=exceptions.BEARER_CHALLENGE
    )
    response = make_client(error).get("/boom")
    assert response.headers["www-authenticate"] == "Bearer"


def test_named_errors_carry_their_status_message_and_headers():
    response = make_client(exceptions.InvalidCredentialsError()).get("/boom")
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"

    response = make_client(exceptions.ProductNotFoundError()).get("/boom")
    assert response.status_code == 404
    assert response.json() == {"detail": "Product is not found."}


def test_a_message_can_override_a_named_errors_default():
    response = make_client(exceptions.ProductNotFoundError("Gone.")).get("/boom")
    assert response.json() == {"detail": "Gone."}


def test_login_failure_keeps_its_challenge_header(client, make_user):
    user = make_user()
    response = client.post(
        "/auth/", data={"username": user.username, "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_a_nul_character_is_a_422_not_a_crash(client, make_user, auth):
    # Postgres cannot store NUL, so the database refuses it. That must not become a 500.
    owner, nul = make_user(), "ab\x00cd"

    login = client.post("/auth/", data={"username": nul, "password": "whatever123"})
    register = client.post(
        "/users/",
        json={
            "username": nul,
            "email": "nul@example.com",
            "password": "StrongPass123!",
        },
    )
    name = client.post(
        "/products/", json={"name": nul, "start_price": 5}, headers=auth(owner)
    )
    description = client.post(
        "/products/",
        json={"name": "a", "description": nul, "start_price": 5},
        headers=auth(owner),
    )

    for response in (login, register, name, description):
        assert response.status_code == 422
        assert response.json() == {
            "detail": "The request contains a value that cannot be stored."
        }
