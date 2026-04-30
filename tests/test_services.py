import pytest

from app.api.schemas.book import BookCreate, BookStatusUpdate
from app.api.schemas.borrow import BorrowCreate
from app.api.schemas.member import MemberCreate, MemberStatusUpdate
from app.database.repositories.book_repository import BookRepository
from app.database.repositories.borrow_repository import BorrowRepository
from app.database.repositories.member_repository import MemberRepository
from app.domain.book import (
    BookNotAvailableError,
    BookRetirementError,
    BookStatus,
    DuplicateISBNError,
)
from app.domain.borrow import BookAlreadyBorrowedError, BookAlreadyReturnedError
from app.domain.member import DuplicateEmailError, MemberNotActiveError, MemberStatus
from app.services.book_service import BookService
from app.services.borrow_service import BorrowService
from app.services.member_service import MemberService


def book_service(db):
    return BookService(BookRepository(db))


def member_service(db):
    return MemberService(MemberRepository(db))


def borrow_service(db):
    return BorrowService(BorrowRepository(db), BookRepository(db), MemberRepository(db))


def test_create_book(db_session):
    svc = book_service(db_session)
    book = svc.create_book(BookCreate(title="The Pragmatic Programmer", author="Hunt & Thomas"))
    assert book.title == "The Pragmatic Programmer"
    assert book.status == "available"


def test_create_member_duplicate_email(db_session):
    svc = member_service(db_session)
    svc.create_member(MemberCreate(name="Alice", email="alice@example.com"))
    with pytest.raises(DuplicateEmailError):
        svc.create_member(MemberCreate(name="Bob", email="alice@example.com"))


def test_create_book_duplicate_isbn(db_session):
    svc = book_service(db_session)
    svc.create_book(BookCreate(title="Book A", author="Author", isbn="9781234567890"))
    with pytest.raises(DuplicateISBNError, match="already registered"):
        svc.create_book(BookCreate(title="Book B", author="Author", isbn="9781234567890"))


def test_update_book_duplicate_isbn(db_session):
    svc = book_service(db_session)
    svc.create_book(BookCreate(title="Book A", author="Author", isbn="9781234567890"))
    book_b = svc.create_book(BookCreate(title="Book B", author="Author", isbn="9780000000000"))
    from app.api.schemas.book import BookUpdate

    with pytest.raises(DuplicateISBNError, match="already registered"):
        svc.update_book(book_b.id, BookUpdate(isbn="9781234567890"))


def test_borrow_book_success(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    member = member_service(db_session).create_member(
        MemberCreate(name="Bob", email="bob@example.com")
    )
    borrow = borrow_service(db_session).borrow_book(
        BorrowCreate(book_id=book.id, member_id=member.id)
    )
    assert borrow.book_id == book.id
    assert borrow.member_id == member.id
    assert borrow.returned_at is None
    assert borrow.due_date is not None


def test_borrow_unavailable_book(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    book_service(db_session).update_status(book.id, BookStatusUpdate(status=BookStatus.RETIRED))
    member = member_service(db_session).create_member(
        MemberCreate(name="Carol", email="carol@example.com")
    )
    with pytest.raises(BookNotAvailableError):
        borrow_service(db_session).borrow_book(BorrowCreate(book_id=book.id, member_id=member.id))


def test_borrow_by_inactive_member(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    member = member_service(db_session).create_member(
        MemberCreate(name="Dan", email="dan@example.com")
    )
    member_service(db_session).update_status(
        member.id, MemberStatusUpdate(status=MemberStatus.INACTIVE)
    )
    with pytest.raises(MemberNotActiveError):
        borrow_service(db_session).borrow_book(BorrowCreate(book_id=book.id, member_id=member.id))


def test_borrow_already_borrowed_book(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    m1 = member_service(db_session).create_member(MemberCreate(name="Eve", email="eve@example.com"))
    m2 = member_service(db_session).create_member(
        MemberCreate(name="Frank", email="frank@example.com")
    )
    borrow_service(db_session).borrow_book(BorrowCreate(book_id=book.id, member_id=m1.id))
    with pytest.raises((BookNotAvailableError, BookAlreadyBorrowedError)):
        borrow_service(db_session).borrow_book(BorrowCreate(book_id=book.id, member_id=m2.id))


def test_return_book_success(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    member = member_service(db_session).create_member(
        MemberCreate(name="Grace", email="grace@example.com")
    )
    borrow = borrow_service(db_session).borrow_book(
        BorrowCreate(book_id=book.id, member_id=member.id)
    )

    returned = borrow_service(db_session).return_book(borrow.id)
    assert returned.returned_at is not None

    refreshed = book_service(db_session).get_book(book.id)
    assert refreshed.status == "available"


def test_return_already_returned(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    member = member_service(db_session).create_member(
        MemberCreate(name="Heidi", email="heidi@example.com")
    )
    borrow = borrow_service(db_session).borrow_book(
        BorrowCreate(book_id=book.id, member_id=member.id)
    )
    borrow_service(db_session).return_book(borrow.id)
    with pytest.raises(BookAlreadyReturnedError):
        borrow_service(db_session).return_book(borrow.id)


def test_update_book_partial(db_session):
    svc = book_service(db_session)
    book = svc.create_book(BookCreate(title="Original", author="Author", genre="Sci-Fi"))
    from app.api.schemas.book import BookUpdate

    updated = svc.update_book(book.id, BookUpdate(title="Updated Title"))
    assert updated.title == "Updated Title"
    assert updated.author == "Author"
    assert updated.genre == "Sci-Fi"


def test_update_book_full(db_session):
    svc = book_service(db_session)
    book = svc.create_book(BookCreate(title="Original", author="Author"))
    from app.api.schemas.book import BookUpdate

    updated = svc.update_book(book.id, BookUpdate(title="New", author="New Author", genre="Drama"))
    assert updated.title == "New"
    assert updated.author == "New Author"
    assert updated.genre == "Drama"


def test_update_member_partial(db_session):
    svc = member_service(db_session)
    member = svc.create_member(
        MemberCreate(name="Alice", email="alice@example.com", phone="555-1234")
    )
    from app.api.schemas.member import MemberUpdate

    updated = svc.update_member(member.id, MemberUpdate(phone="555-9999"))
    assert updated.phone == "555-9999"
    assert updated.name == "Alice"
    assert updated.email == "alice@example.com"


def test_update_member_duplicate_email(db_session):
    svc = member_service(db_session)
    svc.create_member(MemberCreate(name="Alice", email="alice@example.com"))
    bob = svc.create_member(MemberCreate(name="Bob", email="bob@example.com"))
    from app.api.schemas.member import MemberUpdate

    with pytest.raises(DuplicateEmailError, match="already registered"):
        svc.update_member(bob.id, MemberUpdate(email="alice@example.com"))


def test_update_member_same_email_no_conflict(db_session):
    svc = member_service(db_session)
    member = svc.create_member(MemberCreate(name="Alice", email="alice@example.com"))
    from app.api.schemas.member import MemberUpdate

    updated = svc.update_member(member.id, MemberUpdate(email="alice@example.com", name="Alice B"))
    assert updated.email == "alice@example.com"
    assert updated.name == "Alice B"


def test_book_status_transition_retire(db_session):
    svc = book_service(db_session)
    book = svc.create_book(BookCreate(title="Old Book", author="Someone"))
    retired = svc.update_status(book.id, BookStatusUpdate(status=BookStatus.RETIRED))
    assert retired.status == "retired"


def test_book_status_transition_retire_borrowed(db_session):
    book = book_service(db_session).create_book(BookCreate(title="SICP", author="Abelson"))
    member = member_service(db_session).create_member(
        MemberCreate(name="Ivan", email="ivan@example.com")
    )
    borrow_service(db_session).borrow_book(BorrowCreate(book_id=book.id, member_id=member.id))
    with pytest.raises(BookRetirementError):
        book_service(db_session).update_status(book.id, BookStatusUpdate(status=BookStatus.RETIRED))
