from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.api.schemas.book import BookCreate, BookStatusUpdate, BookUpdate
from app.database.models.book import Book
from app.database.repositories.book_repository import BookRepository
from app.domain.book import (
    BookNotFoundError,
    BookStatus,
    DuplicateISBNError,
    validate_book_status_transition,
)


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self.repo = repo

    def create_book(self, data: BookCreate) -> Book:
        """Add a new book to the library."""
        try:
            book = self.repo.create(data.model_dump())
            self.repo.db.commit()
        except IntegrityError as ie:
            self.repo.db.rollback()
            raise DuplicateISBNError(f"ISBN '{data.isbn}' is already registered") from ie
        self.repo.db.refresh(book)
        return book

    def get_book(self, book_id: UUID) -> Book:
        """Fetch a book by ID or raise BookNotFoundError."""
        book = self.repo.get_by_id(book_id)
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
        return self.repo.get_all(page=page, size=size, status=status, search=search)

    def replace_book(self, book_id: UUID, data: BookUpdate) -> Book:
        """Full replacement — all fields written, unset fields cleared to None (PUT)."""
        self.get_book(book_id)
        try:
            book = self.repo.update(book_id, data.model_dump())
            self.repo.db.commit()
        except IntegrityError as ie:
            self.repo.db.rollback()
            raise DuplicateISBNError(f"ISBN '{data.isbn}' is already registered") from ie
        self.repo.db.refresh(book)
        return book

    def update_book(self, book_id: UUID, data: BookUpdate) -> Book:
        """Partial update — only provided fields written, others left unchanged (PATCH)."""
        self.get_book(book_id)
        updates = data.model_dump(exclude_unset=True)
        try:
            book = self.repo.update(book_id, updates)
            self.repo.db.commit()
        except IntegrityError as ie:
            self.repo.db.rollback()
            raise DuplicateISBNError(f"ISBN '{updates.get('isbn')}' is already registered") from ie
        self.repo.db.refresh(book)
        return book

    def update_status(self, book_id: UUID, data: BookStatusUpdate) -> Book:
        """Change book status. Domain layer validates the transition."""
        book = self.get_book(book_id)
        validate_book_status_transition(BookStatus(book.status), data.status)
        book = self.repo.update_status(book_id, data.status.value)
        self.repo.db.commit()
        self.repo.db.refresh(book)
        return book
