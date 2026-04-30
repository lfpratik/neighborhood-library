from enum import StrEnum


class BookStatus(StrEnum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RETIRED = "retired"


BOOK_STATUS_TRANSITIONS = {
    BookStatus.AVAILABLE: {BookStatus.BORROWED, BookStatus.RETIRED},
    BookStatus.BORROWED: {BookStatus.AVAILABLE},
    BookStatus.RETIRED: set(),  # terminal state
}


class BookDomainError(Exception):
    """Base domain error for books."""


class BookNotFoundError(BookDomainError):
    """Book with given ID does not exist."""


class BookNotAvailableError(BookDomainError):
    """Book cannot be borrowed (already borrowed or retired)."""


class BookRetirementError(BookDomainError):
    """Book cannot be retired (currently borrowed)."""


class InvalidBookStatusTransitionError(BookDomainError):
    """Invalid status transition attempted."""


class DuplicateISBNError(BookDomainError):
    """A book with this ISBN already exists."""


def validate_book_is_available(status: BookStatus) -> None:
    """Validate that a book can be borrowed."""
    if status != BookStatus.AVAILABLE:
        raise BookNotAvailableError(f"Book is currently '{status.value}' and cannot be borrowed")


def validate_book_status_transition(current: BookStatus, new: BookStatus) -> None:
    """Validate that a book status transition is allowed."""

    # Explicit business rule

    if current == BookStatus.BORROWED and new == BookStatus.RETIRED:
        raise BookRetirementError("Book must be returned before retiring")

    allowed = BOOK_STATUS_TRANSITIONS.get(current, set())

    if new not in allowed:
        raise InvalidBookStatusTransitionError(
            f"Cannot transition from '{current.value}' to '{new.value}'"
        )
