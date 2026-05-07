from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.api.schemas.book import BookCreate, BookStatusUpdate, BookUpdate
from app.database.models.book import Book
from app.domain.book import (
    BookNotFoundError,
    BookStatus,
    DuplicateISBNError,
    validate_book_status_transition,
)
from app.services import BaseService

if TYPE_CHECKING:
    from app.database.unit_of_work import UnitOfWork


class BookService(BaseService):
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create_book(self, data: BookCreate) -> Book:
        """Add a new book to the library."""
        try:
            book = self.uow.books.create(data.model_dump())
        except IntegrityError as ie:
            isbn = data.isbn
            raise DuplicateISBNError(
                f"ISBN '{isbn}' is already registered" if isbn else "ISBN already registered"
            ) from ie

        self.logger.info("book_created", book_id=str(book.id), title=book.title, isbn=book.isbn)
        return book

    def get_book(self, book_id: UUID) -> Book:
        """Fetch a book by ID or raise BookNotFoundError."""
        book = self.uow.books.get_by_id(book_id)
        if book is None:
            raise BookNotFoundError(f"Book {book_id} not found")
        return book

    def list_books(
        self,
        page: int,
        size: int,
        status: str | None = None,
        search: str | None = None,
    ) -> tuple[list[Book], int]:
        """List books with optional status and search filters."""
        return self.uow.books.get_all(page=page, size=size, status=status, search=search)

    def replace_book(self, book_id: UUID, data: BookUpdate) -> Book:
        """Full replacement — all fields written, unset fields cleared to None (PUT)."""
        self.get_book(book_id)
        try:
            book = self.uow.books.update(book_id, data.model_dump(exclude_unset=False))
        except IntegrityError as ie:
            isbn = data.isbn
            raise DuplicateISBNError(
                f"ISBN '{isbn}' is already registered" if isbn else "ISBN already registered"
            ) from ie

        self.logger.info("book_replaced", book_id=str(book_id), title=book.title)
        return book

    def update_book(self, book_id: UUID, data: BookUpdate) -> Book:
        """Partial update — only provided fields written, others left unchanged (PATCH)."""
        self.get_book(book_id)
        updates = data.model_dump(exclude_unset=True)
        try:
            book = self.uow.books.update(book_id, updates)
        except IntegrityError as ie:
            isbn = updates.get("isbn")
            raise DuplicateISBNError(
                f"ISBN '{isbn}' is already registered" if isbn else "ISBN already registered"
            ) from ie

        self.logger.info("book_updated", book_id=str(book_id), fields=list(updates.keys()))
        return book

    def update_status(self, book_id: UUID, data: BookStatusUpdate) -> Book:
        """Change book status. Domain layer validates the transition."""
        book = self.get_book(book_id)
        old_status = book.status
        validate_book_status_transition(BookStatus(book.status), data.status)
        updated = self.uow.books.update_status(book_id, data.status.value)

        self.logger.info(
            "book_status_changed",
            book_id=str(book_id),
            from_status=old_status,
            to_status=data.status.value,
        )
        return updated
