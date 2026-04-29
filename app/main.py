import re

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.books import router as books_router
from app.api.routes.borrows import router as borrows_router
from app.api.routes.members import router as members_router
from app.config import settings
from app.dependencies import get_db
from app.domain.book import BookNotAvailableError, BookNotFoundError, BookRetirementError
from app.domain.borrow import (
    BookAlreadyBorrowedError,
    BookAlreadyReturnedError,
    BorrowNotFoundError,
)
from app.domain.member import MemberNotActiveError, MemberNotFoundError


def _not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"detail": {"code": type(exc).__name__, "message": str(exc)}},
    )


def _conflict_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": {"code": type(exc).__name__, "message": str(exc)}},
    )


def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    field = ".".join(str(loc) for loc in first["loc"] if loc != "body")
    raw_msg = first.get("msg", "Validation error")
    message = re.sub(r"^value error,\s*", "", raw_msg, flags=re.IGNORECASE)
    return JSONResponse(
        status_code=422,
        content={"detail": {"code": "ValidationError", "message": f"{field}: {message}" if field else message}},
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Neighborhood Library Management System",
        description="Clean Architecture API for Library Management",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(books_router, prefix="/api/v1")
    app.include_router(members_router, prefix="/api/v1")
    app.include_router(borrows_router, prefix="/api/v1")

    not_found: list[type[Exception]] = [BookNotFoundError, MemberNotFoundError, BorrowNotFoundError]
    for exc_class in not_found:
        app.add_exception_handler(exc_class, _not_found_handler)

    conflict: list[type[Exception]] = [
        BookNotAvailableError,
        BookRetirementError,
        BookAlreadyBorrowedError,
        BookAlreadyReturnedError,
        MemberNotActiveError,
        ValueError,
    ]
    for exc_class in conflict:
        app.add_exception_handler(exc_class, _conflict_handler)

    app.add_exception_handler(RequestValidationError, _validation_handler)

    return app


app = create_app()


@app.get("/api/v1/health")
def health_check() -> dict:
    """Health check endpoint that pings the database."""
    db: Session = next(get_db())
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    finally:
        db.close()
    return {"status": "ok", "database": db_status}
