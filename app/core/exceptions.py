"""Errors raised by services, policies and dependencies.

They carry no web framework types, so the business layer does not depend on
FastAPI. The handler registered in app/main.py turns them into HTTP responses.
"""

from typing import Any

BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


class AppError(Exception):
    status_code = 500
    default_detail: str | None = None
    default_headers: dict[str, str] | None = None

    def __init__(
        self,
        detail: str | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.detail = self.default_detail if detail is None else detail
        self.headers = self.default_headers if headers is None else headers
        super().__init__(self.detail)


class BadRequestError(AppError):
    status_code = 400


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class PayloadTooLargeError(AppError):
    status_code = 413


class UnprocessableError(AppError):
    status_code = 422


# Named errors, only for messages that are raised from more than one place.


class InvalidCredentialsError(UnauthorizedError):
    default_detail = "Could not validate credentials"
    default_headers = BEARER_CHALLENGE


class PermissionDeniedError(ForbiddenError):
    default_detail = "You do not have permission to perform this action."


class NotProductOwnerError(ForbiddenError):
    default_detail = "You are not the owner of this product."


class ProductNotFoundError(NotFoundError):
    default_detail = "Product is not found."


class UserNotFoundError(NotFoundError):
    default_detail = "User is not found."


class StatusRequestNotFoundError(NotFoundError):
    default_detail = "Status request is not found."


class SameStatusError(ConflictError):
    default_detail = "The requested status is the same as the current status."


class StatusRequestProductChangedError(ConflictError):
    default_detail = "Status request product has changed."


class StatusRequestAlreadyProcessedError(ConflictError):
    default_detail = "This status request has already been processed."


class InvalidResetTokenError(BadRequestError):
    default_detail = "Invalid password reset token"


class ResetTokenAlreadyUsedError(BadRequestError):
    default_detail = "Password reset token has already been used"
