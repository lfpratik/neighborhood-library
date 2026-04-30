"""
Logging infrastructure — configure once, use everywhere.

Public surface:
  configure_logging(log_level, environment)  — call at app startup
  LoggerMixin                                — add self.logger to any class
  log_db_call(event_name)                    — repository-only decorator
  audit                                      — separate audit logger for services
"""

from __future__ import annotations

import logging
import sys
import time
from functools import cached_property, wraps
from typing import Callable

import structlog

# ---------------------------------------------------------------------------
# Audit logger — ready to use when needed.
# Import in services only: from app.core.logging import audit
# In production, route the "audit" logger to a separate handler
# (file, SIEM, compliance sink) without changing any calling code.
# ---------------------------------------------------------------------------
audit: structlog.stdlib.BoundLogger = structlog.get_logger("audit")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def configure_logging(log_level: str = "INFO", environment: str = "development") -> None:
    """Configure structlog and stdlib logging.  Call once at application startup.

    Dev:  coloured, human-readable output via ConsoleRenderer.
    Prod: machine-readable JSON — one compact line per event, ready for
          Loki / Datadog / CloudWatch.

    structlog.contextvars.merge_contextvars pulls request_id, method, and path
    (bound by RequestLoggingMiddleware) into every log record automatically —
    no manual passing through service or repository call stacks.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    is_production = environment == "production"

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,   # request_id, method, path
        structlog.stdlib.add_logger_name,           # which class / module
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_production:
        processors = shared_processors + [
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib loggers (uvicorn, sqlalchemy, alembic) through the same pipeline.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    # Silence uvicorn's built-in access log in all environments — our
    # RequestLoggingMiddleware replaces it with structured request_completed logs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    if is_production:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# LoggerMixin
# ---------------------------------------------------------------------------

class LoggerMixin:
    """Provides self.logger bound to the concrete class name.

    Uses cached_property so the logger is created once on first access —
    no super().__init__() required in subclasses.

    Usage:
        class BookService(BaseService):          # BaseService(LoggerMixin)
            def create_book(self, data):
                ...
                self.logger.info("book_created", book_id=str(book.id))
    """

    @cached_property
    def logger(self) -> structlog.stdlib.BoundLogger:
        return structlog.get_logger(self.__class__.__name__)


# ---------------------------------------------------------------------------
# @log_db_call — repository decorator
# ---------------------------------------------------------------------------

def log_db_call(event_name: str) -> Callable:
    """Decorator for repository methods only.

    Logs three events per call:
      {event_name}_started  — DEBUG, at method entry
      {event_name}_success  — DEBUG, on success with duration_ms
      {event_name}_failed   — WARNING, on any exception with duration_ms and error detail

    Business semantics are deliberately absent — use meaningful event names
    (e.g. "db_create_book", "db_update_member_status") so log queries are specific,
    but keep the content to DB-layer facts only.

    Context vars (request_id, method, path) are propagated automatically by
    structlog.contextvars, so every repository log line carries the request_id
    bound by the middleware without any manual passing.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: LoggerMixin, *args, **kwargs):
            self.logger.debug(f"{event_name}_started")
            start = time.perf_counter()
            try:
                result = func(self, *args, **kwargs)
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                self.logger.debug(f"{event_name}_success", duration_ms=duration_ms)
                return result
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                self.logger.warning(
                    f"{event_name}_failed",
                    duration_ms=duration_ms,
                    exc_type=type(exc).__name__,
                    exc_msg=str(exc),
                )
                raise

        return wrapper

    return decorator
