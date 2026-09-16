from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """Standard error shape shared with `backend` — see docs/API_CONTRACTS.md."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None, status_code: int = 400):
        self.code = code
        self.message = message
        self.details = details
        self.status_code = status_code


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "details": exc.details},
    )
