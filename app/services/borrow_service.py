from datetime import UTC, datetime
from uuid import UUID

from app.api.schemas.borrow import BorrowCreate
from app.database.models.borrow import Borrow
from app.database.repositories.book_repository import BookRepository
from app.database.repositories.borrow_repository import BorrowRepository
from app.database.repositories.member_repository import MemberRepository
from app.domain.book import BookNotAvailableError, BookNotFoundError, BookStatus
from app.domain.borrow import (
    BookAlreadyBorrowedError,
    BorrowNotFoundError,
    calculate_due_date,
    validate_borrow_is_active,
)
from app.domain.member import MemberNotActiveError, MemberNotFoundError, MemberStatus


class BorrowService:
    def __init__(
        self,
        borrow_repo: BorrowRepository,
        book_repo: BookRepository,
        member_repo: MemberRepository,
    ) -> None:
        self.borrow_repo = borrow_repo
        self.book_repo = book_repo
        self.member_repo = member_repo

    def borrow_book(self, data: BorrowCreate) -> Borrow:
        """Record a book borrow. Domain layer validates all rules."""
        book = self.book_repo.get_by_id(data.book_id)
        if book is None:
            raise BookNotFoundError(f"Book {data.book_id} not found")
        if book.status != BookStatus.AVAILABLE.value:
            raise BookNotAvailableError(f"Book is currently {book.status}")

        member = self.member_repo.get_by_id(data.member_id)
        if member is None:
            raise MemberNotFoundError(f"Member {data.member_id} not found")
        if member.status != MemberStatus.ACTIVE.value:
            raise MemberNotActiveError(f"Member is {member.status}")

        if self.borrow_repo.get_active_by_book_id(data.book_id) is not None:
            raise BookAlreadyBorrowedError("Book already has an active borrow")

        borrowed_at = datetime.now(UTC)
        due_date = calculate_due_date(borrowed_at)
        borrow = self.borrow_repo.create(
            {
                "book_id": data.book_id,
                "member_id": data.member_id,
                "borrowed_at": borrowed_at,
                "due_date": due_date,
                "notes": data.notes,
            }
        )
        self.book_repo.update_status(data.book_id, BookStatus.BORROWED.value)
        self.borrow_repo.db.commit()
        return self.borrow_repo.get_by_id(borrow.id)  # type: ignore[return-value]

    def return_book(self, borrow_id: UUID) -> Borrow:
        """Return a borrowed book. Domain layer validates it's still active."""
        borrow = self.borrow_repo.get_by_id(borrow_id)
        if borrow is None:
            raise BorrowNotFoundError(f"Borrow {borrow_id} not found")
        validate_borrow_is_active(borrow.returned_at)

        self.borrow_repo.update_returned_at(borrow_id, datetime.now(UTC))
        self.book_repo.update_status(borrow.book_id, BookStatus.AVAILABLE.value)
        self.borrow_repo.db.commit()
        return self.borrow_repo.get_by_id(borrow_id)  # type: ignore[return-value]

    def get_borrow(self, borrow_id: UUID) -> Borrow:
        """Fetch a borrow by ID or raise BorrowNotFoundError."""
        borrow = self.borrow_repo.get_by_id(borrow_id)
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
        return self.borrow_repo.get_all(
            page=page,
            size=size,
            member_id=member_id,
            book_id=book_id,
            active=active,
            overdue=overdue,
        )
