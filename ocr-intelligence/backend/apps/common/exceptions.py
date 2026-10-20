import logging

from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.views import exception_handler

from .responses import error_response

logger = logging.getLogger(__name__)


class ApiError(exceptions.APIException):
    """Domain error rendered through the unified envelope."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "bad_request"

    def __init__(self, message: str, code: str | None = None, status_code: int | None = None, details=None):
        super().__init__(detail=message, code=code or self.default_code)
        if status_code is not None:
            self.status_code = status_code
        self.details = details


def _flatten_validation(detail):
    """Turn DRF's nested validation structure into a human-readable first message."""
    if isinstance(detail, dict):
        for key, value in detail.items():
            inner = _flatten_validation(value)
            if inner:
                return inner if key in {"non_field_errors", "detail"} else f"{key}: {inner}"
    elif isinstance(detail, (list, tuple)):
        for value in detail:
            inner = _flatten_validation(value)
            if inner:
                return inner
    elif detail:
        return str(detail)
    return ""


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    response = exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled API error", exc_info=exc)
        return error_response("server_error", "Internal server error.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, ApiError):
        return error_response(exc.detail.code, str(exc.detail), exc.status_code, exc.details)
    if isinstance(exc, exceptions.ValidationError):
        message = _flatten_validation(exc.detail) or "Validation failed."
        return error_response("validation_error", message, response.status_code, exc.detail)
    message = str(exc.detail) if hasattr(exc, "detail") else "Request failed."
    return error_response(getattr(exc, "default_code", "error"), message, response.status_code)
