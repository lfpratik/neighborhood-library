from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.schemas.book import BookCreate, BookResponse, BookStatusUpdate, BookUpdate
from app.api.schemas.common import PaginatedResponse
from app.dependencies import get_book_service
from app.domain.book import BookStatus
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_book(
    data: BookCreate,
    request: Request,
    response: Response,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Add a new book to the library."""
    book = service.create_book(data)
    response.headers["Location"] = str(request.url_for("get_book", book_id=book.id))
    return BookResponse.model_validate(book)


@router.get("")
def list_books(
    status: BookStatus | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 20,
    service: BookService = Depends(get_book_service),
) -> PaginatedResponse[BookResponse]:
    """List books with optional status filter and search."""
    items, total = service.list_books(
        page=page,
        size=size,
        status=status.value if status else None,
        search=search,
    )
    return PaginatedResponse(
        items=[BookResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )


@router.get("/{book_id}", name="get_book")
def get_book(
    book_id: UUID,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Get book detail by ID."""
    book = service.get_book(book_id)
    return BookResponse.model_validate(book)


@router.put("/{book_id}")
def update_book(
    book_id: UUID,
    data: BookUpdate,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Update book information."""
    book = service.update_book(book_id, data)
    return BookResponse.model_validate(book)


@router.patch("/{book_id}/status")
def update_book_status(
    book_id: UUID,
    data: BookStatusUpdate,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Change book status."""
    book = service.update_status(book_id, data)
    return BookResponse.model_validate(book)
