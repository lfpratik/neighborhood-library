from datetime import UTC, datetime, timedelta

import pytest

from app.domain.book import (
    BookNotAvailableError,
    BookRetirementError,
    BookStatus,
    InvalidBookStatusTransitionError,
    validate_book_status_transition,
)
from app.domain.borrow import (
    BookAlreadyReturnedError,
    calculate_due_date,
    is_overdue,
    validate_borrow_is_active,
)
from app.domain.member import (
    InvalidMemberStatusTransitionError,
    MemberStatus,
    validate_member_status_transition,
)


def test_valid_book_transitions():
    validate_book_status_transition(BookStatus.AVAILABLE, BookStatus.BORROWED)
    validate_book_status_transition(BookStatus.AVAILABLE, BookStatus.RETIRED)
    validate_book_status_transition(BookStatus.BORROWED, BookStatus.AVAILABLE)


def test_invalid_book_transition_retired_to_available():
    with pytest.raises(InvalidBookStatusTransitionError):
        validate_book_status_transition(BookStatus.RETIRED, BookStatus.AVAILABLE)


def test_invalid_book_transition_borrowed_to_retired():
    with pytest.raises(BookRetirementError):
        validate_book_status_transition(BookStatus.BORROWED, BookStatus.RETIRED)


def test_valid_member_transitions():
    validate_member_status_transition(MemberStatus.ACTIVE, MemberStatus.INACTIVE)
    validate_member_status_transition(MemberStatus.ACTIVE, MemberStatus.SUSPENDED)
    validate_member_status_transition(MemberStatus.INACTIVE, MemberStatus.ACTIVE)
    validate_member_status_transition(MemberStatus.SUSPENDED, MemberStatus.ACTIVE)


def test_invalid_member_transition_inactive_to_suspended():
    with pytest.raises(InvalidMemberStatusTransitionError):
        validate_member_status_transition(MemberStatus.INACTIVE, MemberStatus.SUSPENDED)


def test_calculate_due_date():
    borrowed_at = datetime(2024, 1, 1, tzinfo=UTC)
    due_date = calculate_due_date(borrowed_at)
    assert due_date == datetime(2024, 1, 15, tzinfo=UTC)


def test_is_overdue_past_due_not_returned():
    past_due = datetime.now(UTC) - timedelta(days=1)
    assert is_overdue(past_due, None) is True


def test_is_overdue_past_due_already_returned():
    past_due = datetime.now(UTC) - timedelta(days=1)
    returned = datetime.now(UTC)
    assert is_overdue(past_due, returned) is False


def test_is_overdue_not_yet_due():
    future_due = datetime.now(UTC) + timedelta(days=5)
    assert is_overdue(future_due, None) is False


def test_validate_borrow_is_active_passes_when_not_returned():
    validate_borrow_is_active(None)  # should not raise


def test_validate_borrow_is_active_raises_when_returned():
    with pytest.raises(BookAlreadyReturnedError):
        validate_borrow_is_active(datetime.now(UTC))
