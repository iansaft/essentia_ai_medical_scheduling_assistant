from __future__ import annotations

from uuid import uuid4

import structlog
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Propagate X-Correlation-ID across the request lifecycle.

    Accepts an inbound correlation id when present (e.g. from n8n),
    otherwise generates one. Binds it to structlog contextvars so every
    log line emitted while handling the request carries the id, and
    echoes it on the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        incoming = request.headers.get(CORRELATION_ID_HEADER)
        correlation_id = incoming.strip() if incoming else ""
        if not correlation_id:
            correlation_id = str(uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
