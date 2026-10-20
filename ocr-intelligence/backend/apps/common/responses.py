"""Unified API envelope: {"success": bool, "data": ..., "error": {"code", "message", "details"} | null}."""
from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success_response(data: Any = None, status_code: int = status.HTTP_200_OK) -> Response:
    return Response({"success": True, "data": data, "error": None}, status=status_code)


def error_response(
    code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Any = None
) -> Response:
    return Response(
        {"success": False, "data": None, "error": {"code": code, "message": message, "details": details}},
        status=status_code,
    )
