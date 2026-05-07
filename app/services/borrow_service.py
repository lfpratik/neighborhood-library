from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.api.schemas.borrow import BorrowCreate
from app.database.models.borrow import Borrow
from app.domain.book import BookNotFoundError, BookStatus, validate_book_is_available
from app.domain.borrow import (
    BookAlreadyBorrowedError,
    BorrowNotFoundError,
    calculate_due_date,
    is_overdue,
    validate_borrow_is_active,
)
from app.domain.member import MemberNotFoundError, MemberStatus, validate_member_is_active
from app.services import BaseService

if TYPE_CHECKING:
    from app.database.unit_of_work import UnitOfWork


class BorrowService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def borrow_book(self, data: BorrowCreate) -> Borrow:
        """Record a book borrow. Domain layer validates all rules."""
        book = self.uow.books.get_by_id(data.book_id)
        if book is None:
            raise BookNotFoundError(f"Book {data.book_id} not found")
        validate_book_is_available(BookStatus(book.status))

        member = self.uow.members.get_by_id(data.member_id)
        if member is None:
            raise MemberNotFoundError(f"Member {data.member_id} not found")
        validate_member_is_active(MemberStatus(member.status))

        # Fast-fail (not the real guard — DB constraint is)
        if self.uow.borrows.get_active_by_book_id(data.book_id) is not None:
            raise BookAlreadyBorrowedError("Book already has an active borrow")

        borrowed_at = datetime.now(UTC)
        try:
            borrow = self.uow.borrows.create(
                {
                    "book_id": data.book_id,
                    "member_id": data.member_id,
                    "borrowed_at": borrowed_at,
                    "due_date": calculate_due_date(borrowed_at),
                    "notes": data.notes,
                }
            )
            self.uow.books.update_status(data.book_id, BookStatus.BORROWED.value)
        except IntegrityError as ie:
            raise BookAlreadyBorrowedError("Book already has an active borrow") from ie

        self.logger.info(
            "borrow_created",
            borrow_id=str(borrow.id),
            book_id=str(borrow.book_id),
            member_id=str(borrow.member_id),
            due_date=borrow.due_date.isoformat(),
        )
        return borrow

    def return_book(self, borrow_id: UUID) -> Borrow:
        """Return a borrowed book. Domain layer validates it's still active."""
        borrow = self.uow.borrows.get_by_id(borrow_id)
        if borrow is None:
            raise BorrowNotFoundError(f"Borrow {borrow_id} not found")

        validate_borrow_is_active(borrow.returned_at)

        was_overdue = is_overdue(borrow.due_date, borrow.returned_at)
        self.uow.borrows.update_returned_at(borrow_id, datetime.now(UTC))
        self.uow.books.update_status(borrow.book_id, BookStatus.AVAILABLE.value)

        self.logger.info(
            "borrow_returned",
            borrow_id=str(borrow_id),
            book_id=str(borrow.book_id),
            member_id=str(borrow.member_id),
            overdue=was_overdue,
        )
        return borrow

    def get_borrow(self, borrow_id: UUID) -> Borrow:
        """Fetch a borrow by ID or raise BorrowNotFoundError."""
        borrow = self.uow.borrows.get_by_id(borrow_id)
        if borrow is None:
            raise BorrowNotFoundError(f"Borrow {borrow_id} not found")
        return borrow

    def list_borrows(
        self,
        page: int,
        size: int,
        member_id: UUID | None = None,
        book_id: UUID | None = None,
        active: bool | None = None,
        overdue: bool | None = None,
    ) -> tuple[list[Borrow], int]:
        """List borrows with optional member/book/active/overdue filters."""
        return self.uow.borrows.get_all(
            page=page,
            size=size,
            member_id=member_id,
            book_id=book_id,
            active=active,
            overdue=overdue,
        )
