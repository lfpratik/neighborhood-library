from datetime import UTC, datetime, timedelta

LOAN_PERIOD_DAYS = 14


class BorrowNotFoundError(Exception):
    """Borrow record with given ID does not exist."""


class BookAlreadyBorrowedError(Exception):
    """Book is already borrowed by another member."""


class BookAlreadyReturnedError(Exception):
    """This borrow has already been returned."""


def calculate_due_date(borrowed_at: datetime) -> datetime:
    """Calculate due date from borrow date."""
    return borrowed_at + timedelta(days=LOAN_PERIOD_DAYS)


def is_overdue(due_date: datetime, returned_at: datetime | None) -> bool:
    """Check if a borrow is overdue (past due and not yet returned)."""
    if returned_at is not None:
        return False
    return datetime.now(UTC) > due_date


def validate_borrow_is_active(returned_at: datetime | None) -> None:
    """Validate that a borrow has not already been returned. Raises on invalid."""
    if returned_at is not None:
        raise BookAlreadyReturnedError("This book has already been returned")
