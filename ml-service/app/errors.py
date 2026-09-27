import logging
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("ml_service")


class ApiError(Exception):
    """Standard error shape the frontend handles — `{code, message, details}`, see
    docs/API_CONTRACTS.md."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code


def _error_response(status_code: int, code: str, message: str, details: dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"code": code, "message": message, "details": details})


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


_HTTP_ERROR_CODES = {404: ("NOT_FOUND", "No endpoint exists at this path."), 405: ("METHOD_NOT_ALLOWED", None)}


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    # FastAPI's default is {"detail": ...}, which the frontend's single error path can't read.
    code, message = _HTTP_ERROR_CODES.get(exc.status_code, ("HTTP_ERROR", None))
    response = _error_response(exc.status_code, code, message or str(exc.detail))
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", "-")
    logger.exception("[%s] unhandled error on %s %s", correlation_id, request.method, request.url.path)
    return _error_response(500, "INTERNAL_ERROR", str(exc) or exc.__class__.__name__)
