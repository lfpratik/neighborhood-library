"""Seed database with sample data. Idempotent — safe to run multiple times."""

import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid_utils
from sqlalchemy.orm import Session

from app.database.models.book import Book
from app.database.models.borrow import Borrow
from app.database.models.member import Member
from app.database.session import SessionLocal


def new_id() -> uuid.UUID:
    return uuid.UUID(str(uuid_utils.uuid7()))


NOW = datetime.now(UTC)


def seed() -> None:
    db = SessionLocal()
    try:
        _seed_books(db)
        _seed_members(db)
        _seed_borrows(db)
        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _seed_books(db: Session) -> None:
    books = [
        {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "9780132350884",
            "genre": "Software Engineering",
            "status": "available",
        },
        {
            "title": "Design Patterns",
            "author": "Gang of Four",
            "isbn": "9780201633610",
            "genre": "Software Engineering",
            "status": "borrowed",
        },
        {
            "title": "The Pragmatic Programmer",
            "author": "Andrew Hunt & David Thomas",
            "isbn": "9780135957059",
            "genre": "Software Engineering",
            "status": "available",
        },
        {
            "title": "Refactoring",
            "author": "Martin Fowler",
            "isbn": "9780134757599",
            "genre": "Software Engineering",
            "status": "borrowed",
        },
        {
            "title": "The Mythical Man-Month",
            "author": "Fred Brooks",
            "isbn": "9780201835953",
            "genre": "Software Engineering",
            "status": "retired",
        },
    ]
    for b in books:
        exists = db.query(Book).filter(Book.isbn == b["isbn"]).first()
        if not exists:
            db.add(Book(id=new_id(), **b))
            print(f"  + Book: {b['title']}")
        else:
            print(f"  ~ Book already exists: {b['title']}")


def _seed_members(db: Session) -> None:
    members = [
        {"name": "Alice Johnson", "email": "alice@example.com", "status": "active"},
        {"name": "Bob Smith", "email": "bob@example.com", "status": "inactive"},
        {"name": "Charlie Brown", "email": "charlie@example.com", "status": "suspended"},
    ]
    for m in members:
        exists = db.query(Member).filter(Member.email == m["email"]).first()
        if not exists:
            db.add(Member(id=new_id(), **m))
            print(f"  + Member: {m['name']}")
        else:
            print(f"  ~ Member already exists: {m['name']}")

    db.flush()


def _seed_borrows(db: Session) -> None:
    alice = db.query(Member).filter(Member.email == "alice@example.com").first()
    clean_code = db.query(Book).filter(Book.isbn == "9780132350884").first()
    design_patterns = db.query(Book).filter(Book.isbn == "9780201633610").first()
    refactoring = db.query(Book).filter(Book.isbn == "9780134757599").first()

    # Active normal borrow: Alice borrowed "Refactoring" 5 days ago (due in 9 days)
    _add_borrow(
        db,
        book=refactoring,
        member=alice,
        borrowed_at=NOW - timedelta(days=5),
        due_date=NOW - timedelta(days=5) + timedelta(days=14),
        returned_at=None,
        label="Alice → Refactoring (active, due in 9 days)",
    )

    # Completed borrow: Alice borrowed "Clean Code" 30 days ago, returned 20 days ago
    _add_borrow(
        db,
        book=clean_code,
        member=alice,
        borrowed_at=NOW - timedelta(days=30),
        due_date=NOW - timedelta(days=30) + timedelta(days=14),
        returned_at=NOW - timedelta(days=20),
        label="Alice → Clean Code (returned)",
    )

    # Active overdue borrow: Alice borrowed "Design Patterns" 20 days ago (due 6 days ago)
    _add_borrow(
        db,
        book=design_patterns,
        member=alice,
        borrowed_at=NOW - timedelta(days=20),
        due_date=NOW - timedelta(days=20) + timedelta(days=14),
        returned_at=None,
        label="Alice → Design Patterns (OVERDUE — due 6 days ago)",
    )


def _add_borrow(
    db: Session,
    book: Book | None,
    member: Member | None,
    borrowed_at: datetime,
    due_date: datetime,
    returned_at: datetime | None,
    label: str,
) -> None:
    if book is None or member is None:
        print(f"  ! Skipping borrow (missing book or member): {label}")
        return

    existing = (
        db.query(Borrow)
        .filter(
            Borrow.book_id == book.id,
            Borrow.member_id == member.id,
            Borrow.borrowed_at == borrowed_at,
        )
        .first()
    )
    if existing:
        print(f"  ~ Borrow already exists: {label}")
        return

    db.add(
        Borrow(
            id=new_id(),
            book_id=book.id,
            member_id=member.id,
            borrowed_at=borrowed_at,
            due_date=due_date,
            returned_at=returned_at,
        )
    )
    print(f"  + Borrow: {label}")


if __name__ == "__main__":
    seed()
