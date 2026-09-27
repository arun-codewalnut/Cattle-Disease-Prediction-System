import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.errors import unexpected_error_handler

logger = logging.getLogger("ml_service")

CORRELATION_HEADER = "X-Correlation-Id"


async def correlation_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    try:
        response = await call_next(request)
    except Exception as exc:
        # Handled here rather than only by a top-level Exception handler: that one runs outside
        # CORSMiddleware, so the browser would see a CORS failure instead of the error message.
        response = await unexpected_error_handler(request, exc)
    response.headers[CORRELATION_HEADER] = correlation_id
    return response
