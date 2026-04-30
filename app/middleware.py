import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_logger = structlog.get_logger("middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Structured request/response logging for every HTTP call.

    Per-request lifecycle:
      1. Generate a UUID request_id.
      2. Bind request_id + method + path into structlog contextvars — these keys
         are automatically included in every log line emitted anywhere during
         this request (services, repositories) without manual passing.
      3. Log request_completed (status_code, duration_ms) on success.
      4. Log request_failed (exc_type, duration_ms) on unhandled exception.
      5. Attach X-Request-ID to the response header for client-side correlation.
      6. Clear contextvars so the next request starts with a clean slate.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            _logger.error(
                "request_failed",
                exc_type=type(exc).__name__,
                exc_msg=str(exc),
                duration_ms=duration_ms,
            )
            raise
        finally:
            # Clear after logging so request_id / method / path are present
            # in both request_completed and request_failed log lines.
            structlog.contextvars.clear_contextvars()
