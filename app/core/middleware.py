import logging
import time
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("api.access")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that injects correlation ID and measures request execution time.

    Ensures traceable requests while strictly avoiding logging personal or sensitive data.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"

        # Log request summary without query params or body PII
        logger.info(
            "%s %s - %d (%.4fs) [correlation_id=%s]",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
            correlation_id,
        )

        return response

