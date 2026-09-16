import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

logger = logging.getLogger("ml_service")

CORRELATION_HEADER = "X-Correlation-Id"


async def correlation_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers[CORRELATION_HEADER] = correlation_id
    return response
