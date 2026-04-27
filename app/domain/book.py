from enum import StrEnum


class BookStatus(StrEnum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RETIRED = "retired"


BOOK_STATUS_TRANSITIONS = {
    BookStatus.AVAILABLE: [BookStatus.BORROWED, BookStatus.RETIRED],
    BookStatus.BORROWED: [BookStatus.AVAILABLE],
    BookStatus.RETIRED: [],  # terminal state
}


class BookNotFoundError(Exception):
    """Book with given ID does not exist."""


class BookNotAvailableError(Exception):
    """Book cannot be borrowed (already borrowed or retired)."""


class BookRetirementError(Exception):
    """Book cannot be retired (currently borrowed)."""


def validate_book_status_transition(current: BookStatus, new: BookStatus) -> None:
    """Validate that a book status transition is allowed. Raises on invalid."""
    allowed = BOOK_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed:
        if current == BookStatus.RETIRED:
            raise BookNotAvailableError("Book is retired and cannot change status")
        if current == BookStatus.BORROWED and new == BookStatus.RETIRED:
            raise BookRetirementError("Book must be returned before retiring")
        raise BookNotAvailableError(f"Cannot transition from '{current.value}' to '{new.value}'")
