import re

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.books import router as books_router
from app.api.routes.borrows import router as borrows_router
from app.api.routes.members import router as members_router
from app.config import get_settings
from app.core.logging import configure_logging
from app.database.unit_of_work import UnitOfWork
from app.dependencies import get_uow
from app.domain.book import (
    BookNotAvailableError,
    BookNotFoundError,
    BookRetirementError,
    DuplicateISBNError,
    InvalidBookStatusTransitionError,
)
from app.domain.borrow import (
    BookAlreadyBorrowedError,
    BookAlreadyReturnedError,
    BorrowNotFoundError,
)
from app.domain.member import (
    DuplicateEmailError,
    InvalidMemberStatusTransitionError,
    MemberNotActiveError,
    MemberNotFoundError,
)
from app.middleware import RequestLoggingMiddleware

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = structlog.get_logger("app")
    logger.warning(
        "resource_not_found",
        exc_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=404,
        content={"detail": {"code": type(exc).__name__, "message": str(exc)}},
    )


def _conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = structlog.get_logger("app")
    logger.warning(
        "request_conflict",
        exc_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=409,
        content={"detail": {"code": type(exc).__name__, "message": str(exc)}},
    )


def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger = structlog.get_logger("app")

    first = exc.errors()[0]
    field = ".".join(str(loc) for loc in first["loc"] if loc != "body")
    raw_msg = first.get("msg", "Validation error")
    message = re.sub(r"^value error,\s*", "", raw_msg, flags=re.IGNORECASE)

    logger.warning(
        "validation_error",
        field=field or None,
        message=message,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "code": "ValidationError",
                "message": f"{field}: {message}" if field else message,
            }
        },
    )


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    settings = get_settings()

    # ✅ configure logging here (not at import time)
    configure_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
    )

    logger = structlog.get_logger("app")

    app = FastAPI(
        title="Neighborhood Library Management System",
        description="Clean Architecture API for Library Management",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # Routers
    app.include_router(books_router, prefix=settings.api_v1_prefix)
    app.include_router(members_router, prefix=settings.api_v1_prefix)
    app.include_router(borrows_router, prefix=settings.api_v1_prefix)

    # Exception handlers
    not_found = [BookNotFoundError, MemberNotFoundError, BorrowNotFoundError]
    for exc in not_found:
        app.add_exception_handler(exc, _not_found_handler)

    conflict = [
        BookNotAvailableError,
        BookRetirementError,
        InvalidBookStatusTransitionError,
        BookAlreadyBorrowedError,
        BookAlreadyReturnedError,
        MemberNotActiveError,
        InvalidMemberStatusTransitionError,
        DuplicateEmailError,
        DuplicateISBNError,
    ]
    for exc in conflict:
        app.add_exception_handler(exc, _conflict_handler)

    app.add_exception_handler(RequestValidationError, _validation_handler)

    logger.info(
        "application_started",
        environment=settings.environment,
        log_level=settings.log_level,
    )

    return app


app = create_app()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/v1/health")
def health_check(uow: UnitOfWork = Depends(get_uow)) -> dict:
    try:
        uow.ping()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {"status": "ok", "database": db_status}
