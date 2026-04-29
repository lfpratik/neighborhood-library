from uuid import UUID

from app.api.schemas.book import BookCreate, BookStatusUpdate, BookUpdate
from app.database.models.book import Book
from app.database.repositories.book_repository import BookRepository
from app.domain.book import (
    BookNotFoundError,
    BookRetirementError,
    BookStatus,
    validate_book_status_transition,
)


class BookService:
    def __init__(self, repo: BookRepository) -> None:
        self.repo = repo

    def create_book(self, data: BookCreate) -> Book:
        """Add a new book to the library."""
        if data.isbn and self.repo.get_by_isbn(data.isbn) is not None:
            raise ValueError(f"ISBN '{data.isbn}' is already registered")
        book = self.repo.create(data.model_dump())
        self.repo.db.commit()
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

    def update_book(self, book_id: UUID, data: BookUpdate) -> Book:
        """Replace book information or Partially update mutable book fields (only provided fields)."""
        self.get_book(book_id)
        updates = data.model_dump(exclude_unset=True)
        if "isbn" in updates and updates["isbn"]:
            existing = self.repo.get_by_isbn(updates["isbn"])
            if existing is not None and str(existing.id) != str(book_id):
                raise ValueError(f"ISBN '{updates['isbn']}' is already registered")
        book = self.repo.update(book_id, updates)
        self.repo.db.commit()
        self.repo.db.refresh(book)
        return book

    def update_status(self, book_id: UUID, data: BookStatusUpdate) -> Book:
        """Change book status. Domain layer validates the transition."""
        book = self.get_book(book_id)
        current = BookStatus(book.status)
        new = data.status
        if current == BookStatus.BORROWED and new == BookStatus.RETIRED:
            raise BookRetirementError("Book must be returned before retiring")
        validate_book_status_transition(current, new)
        book = self.repo.update_status(book_id, new.value)
        self.repo.db.commit()
        self.repo.db.refresh(book)
        return book
