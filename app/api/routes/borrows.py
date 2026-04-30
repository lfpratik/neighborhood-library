from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.schemas.borrow import BorrowCreate, BorrowResponse, BorrowSummaryResponse
from app.api.schemas.common import PaginatedResponse
from app.dependencies import get_borrow_service
from app.services.borrow_service import BorrowService

router = APIRouter(prefix="/borrows", tags=["Borrows"])


@router.post("", status_code=status.HTTP_201_CREATED)
def borrow_book(
    data: BorrowCreate,
    request: Request,
    response: Response,
    service: BorrowService = Depends(get_borrow_service),
) -> BorrowResponse:
    """Borrow a book for a member."""
    borrow = service.borrow_book(data)
    response.headers["Location"] = str(request.url_for("get_borrow", borrow_id=borrow.id))
    return BorrowResponse.model_validate(borrow)


@router.get("")
def list_borrows(
    member_id: UUID | None = None,
    book_id: UUID | None = None,
    active: bool | None = None,
    overdue: bool | None = None,
    page: int = 1,
    size: int = 10,
    service: BorrowService = Depends(get_borrow_service),
) -> PaginatedResponse[BorrowSummaryResponse]:
    """List borrows with optional filters."""
    items, total = service.list_borrows(
        page=page,
        size=size,
        member_id=member_id,
        book_id=book_id,
        active=active,
        overdue=overdue,
    )
    return PaginatedResponse(
        items=[BorrowSummaryResponse.model_validate(b) for b in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )


@router.get("/{borrow_id}", name="get_borrow")
def get_borrow(
    borrow_id: UUID,
    service: BorrowService = Depends(get_borrow_service),
) -> BorrowResponse:
    """Get borrow detail by ID."""
    borrow = service.get_borrow(borrow_id)
    return BorrowResponse.model_validate(borrow)


@router.patch("/{borrow_id}/return")
def return_book(
    borrow_id: UUID,
    service: BorrowService = Depends(get_borrow_service),
) -> BorrowResponse:
    """Return a borrowed book."""
    borrow = service.return_book(borrow_id)
    return BorrowResponse.model_validate(borrow)
