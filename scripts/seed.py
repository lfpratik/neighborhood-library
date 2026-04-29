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
        # Available (16)
        {"title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884", "genre": "Software Engineering", "status": "available"},
        {"title": "The Pragmatic Programmer", "author": "Andrew Hunt & David Thomas", "isbn": "9780135957059", "genre": "Software Engineering", "status": "available"},
        {"title": "Working Effectively with Legacy Code", "author": "Michael Feathers", "isbn": "9780131177055", "genre": "Software Engineering", "status": "available"},
        {"title": "Structure and Interpretation of Computer Programs", "author": "Abelson & Sussman", "isbn": "9780262510875", "genre": "Computer Science", "status": "available"},
        {"title": "Introduction to Algorithms", "author": "Cormen, Leiserson, Rivest & Stein", "isbn": "9780262033848", "genre": "Computer Science", "status": "available"},
        {"title": "Code Complete", "author": "Steve McConnell", "isbn": "9780735619678", "genre": "Software Engineering", "status": "available"},
        {"title": "Test-Driven Development", "author": "Kent Beck", "isbn": "9780321146533", "genre": "Software Engineering", "status": "available"},
        {"title": "Continuous Delivery", "author": "Humble & Farley", "isbn": "9780321601919", "genre": "DevOps", "status": "available"},
        {"title": "The Phoenix Project", "author": "Gene Kim, Kevin Behr & George Spafford", "isbn": "9781942788294", "genre": "DevOps", "status": "available"},
        {"title": "Accelerate", "author": "Nicole Forsgren, Jez Humble & Gene Kim", "isbn": "9781942788331", "genre": "DevOps", "status": "available"},
        {"title": "A Philosophy of Software Design", "author": "John Ousterhout", "isbn": "9781732102200", "genre": "Software Engineering", "status": "available"},
        {"title": "Release It!", "author": "Michael Nygard", "isbn": "9781680502398", "genre": "Software Engineering", "status": "available"},
        {"title": "Head First Design Patterns", "author": "Freeman, Robson, Bates & Sierra", "isbn": "9780596007126", "genre": "Software Engineering", "status": "available"},
        {"title": "JavaScript: The Good Parts", "author": "Douglas Crockford", "isbn": "9780596517748", "genre": "Web Development", "status": "available"},
        {"title": "Domain-Driven Design", "author": "Eric Evans", "isbn": "9780321125217", "genre": "Software Architecture", "status": "available"},
        {"title": "The Art of Computer Programming Vol. 1", "author": "Donald Knuth", "isbn": "9780201896831", "genre": "Computer Science", "status": "available"},
        # Borrowed (8) — each matched by an active borrow below
        {"title": "Design Patterns", "author": "Gang of Four", "isbn": "9780201633610", "genre": "Software Engineering", "status": "borrowed"},
        {"title": "Refactoring", "author": "Martin Fowler", "isbn": "9780134757599", "genre": "Software Engineering", "status": "borrowed"},
        {"title": "Site Reliability Engineering", "author": "Beyer, Jones, Petoff & Murphy", "isbn": "9781491929124", "genre": "DevOps", "status": "borrowed"},
        {"title": "Kubernetes in Action", "author": "Marko Lukša", "isbn": "9781617293726", "genre": "DevOps", "status": "borrowed"},
        {"title": "Software Engineering at Google", "author": "Winters, Manshreck & Wright", "isbn": "9781492082798", "genre": "Software Engineering", "status": "borrowed"},
        {"title": "The DevOps Handbook", "author": "Gene Kim, Patrick Debois & John Willis", "isbn": "9781942788003", "genre": "DevOps", "status": "borrowed"},
        {"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "isbn": "9781449373320", "genre": "Data Engineering", "status": "borrowed"},
        {"title": "Building Microservices", "author": "Sam Newman", "isbn": "9781492034025", "genre": "Software Architecture", "status": "borrowed"},
        # Retired (3)
        {"title": "The Mythical Man-Month", "author": "Fred Brooks", "isbn": "9780201835953", "genre": "Software Engineering", "status": "retired"},
        {"title": "Fundamentals of Software Architecture", "author": "Mark Richards & Neal Ford", "isbn": "9781492043454", "genre": "Software Architecture", "status": "retired"},
        {"title": "Clean Architecture", "author": "Robert C. Martin", "isbn": "9780134494166", "genre": "Software Engineering", "status": "retired"},
    ]
    for b in books:
        exists = db.query(Book).filter(Book.isbn == b["isbn"]).first()
        if not exists:
            db.add(Book(id=new_id(), **b))
            print(f"  + Book: {b['title']}")
        else:
            print(f"  ~ Book already exists: {b['title']}")

    db.flush()


def _seed_members(db: Session) -> None:
    members = [
        # Active (7)
        {"name": "Alice Johnson", "email": "alice@example.com", "phone": "555-0101", "status": "active"},
        {"name": "Dave Martinez", "email": "dave@example.com", "phone": "555-0104", "status": "active"},
        {"name": "Eve Williams", "email": "eve@example.com", "phone": "555-0105", "status": "active"},
        {"name": "Frank Chen", "email": "frank@example.com", "phone": "555-0106", "status": "active"},
        {"name": "Grace Kim", "email": "grace@example.com", "phone": "555-0107", "status": "active"},
        {"name": "Henry Patel", "email": "henry@example.com", "phone": "555-0108", "status": "active"},
        {"name": "Iris Thompson", "email": "iris@example.com", "phone": "555-0109", "status": "active"},
        # Inactive (3)
        {"name": "Bob Smith", "email": "bob@example.com", "phone": "555-0102", "status": "inactive"},
        {"name": "Jack Wilson", "email": "jack@example.com", "phone": "555-0110", "status": "inactive"},
        {"name": "Karen Davis", "email": "karen@example.com", "phone": "555-0111", "status": "inactive"},
        # Suspended (2)
        {"name": "Charlie Brown", "email": "charlie@example.com", "phone": "555-0103", "status": "suspended"},
        {"name": "Liam Moore", "email": "liam@example.com", "phone": "555-0112", "status": "suspended"},
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
    def book(isbn: str) -> Book | None:
        return db.query(Book).filter(Book.isbn == isbn).first()

    def member(email: str) -> Member | None:
        return db.query(Member).filter(Member.email == email).first()

    def borrow(days_ago: int) -> tuple[datetime, datetime]:
        borrowed_at = NOW - timedelta(days=days_ago)
        return borrowed_at, borrowed_at + timedelta(days=14)

    borrows: list[dict] = [
        # ── Active borrows (8) — books status = "borrowed" ──────────────────
        # 3 overdue
        {"book": book("9780201633610"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(20))), "returned_at": None,                        "label": "Alice → Design Patterns (OVERDUE, due 6 days ago)"},
        {"book": book("9781492082798"), "member": member("frank@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(18))), "returned_at": None,                        "label": "Frank → Software Engineering at Google (OVERDUE, due 4 days ago)"},
        {"book": book("9781449373320"), "member": member("henry@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(16))), "returned_at": None,                        "label": "Henry → Designing Data-Intensive Applications (OVERDUE, due 2 days ago)"},
        # 5 active (not yet due)
        {"book": book("9780134757599"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(5))),  "returned_at": None,                        "label": "Alice → Refactoring (active, due in 9 days)"},
        {"book": book("9781491929124"), "member": member("dave@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(3))),  "returned_at": None,                        "label": "Dave → Site Reliability Engineering (active, due in 11 days)"},
        {"book": book("9781617293726"), "member": member("eve@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(7))),  "returned_at": None,                        "label": "Eve → Kubernetes in Action (active, due in 7 days)"},
        {"book": book("9781942788003"), "member": member("grace@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(2))),  "returned_at": None,                        "label": "Grace → The DevOps Handbook (active, due in 12 days)"},
        {"book": book("9781492034025"), "member": member("iris@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(1))),  "returned_at": None,                        "label": "Iris → Building Microservices (active, due in 13 days)"},

        # ── Completed borrows (31) ───────────────────────────────────────────
        # Alice (5)
        {"book": book("9780132350884"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(30))),  "returned_at": NOW - timedelta(days=20),   "label": "Alice → Clean Code (returned)"},
        {"book": book("9780321146533"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(60))),  "returned_at": NOW - timedelta(days=50),   "label": "Alice → Test-Driven Development (returned)"},
        {"book": book("9781732102200"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(90))),  "returned_at": NOW - timedelta(days=78),   "label": "Alice → A Philosophy of Software Design (returned)"},
        {"book": book("9781942788294"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(45))),  "returned_at": NOW - timedelta(days=35),   "label": "Alice → The Phoenix Project (returned)"},
        {"book": book("9780596007126"), "member": member("alice@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(120))), "returned_at": NOW - timedelta(days=108),  "label": "Alice → Head First Design Patterns (returned)"},
        # Bob (3)
        {"book": book("9780135957059"), "member": member("bob@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(90))),  "returned_at": NOW - timedelta(days=80),   "label": "Bob → The Pragmatic Programmer (returned)"},
        {"book": book("9780131177055"), "member": member("bob@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(75))),  "returned_at": NOW - timedelta(days=63),   "label": "Bob → Working Effectively with Legacy Code (returned)"},
        {"book": book("9780262033848"), "member": member("bob@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(100))), "returned_at": NOW - timedelta(days=90),   "label": "Bob → Introduction to Algorithms (returned)"},
        # Charlie (3)
        {"book": book("9780735619678"), "member": member("charlie@example.com"), **dict(zip(("borrowed_at","due_date"), borrow(80))),  "returned_at": NOW - timedelta(days=68),   "label": "Charlie → Code Complete (returned)"},
        {"book": book("9780321601919"), "member": member("charlie@example.com"), **dict(zip(("borrowed_at","due_date"), borrow(65))),  "returned_at": NOW - timedelta(days=53),   "label": "Charlie → Continuous Delivery (returned)"},
        {"book": book("9780262510875"), "member": member("charlie@example.com"), **dict(zip(("borrowed_at","due_date"), borrow(50))),  "returned_at": NOW - timedelta(days=38),   "label": "Charlie → Structure and Interpretation of Computer Programs (returned)"},
        # Dave (3)
        {"book": book("9781942788331"), "member": member("dave@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(55))),  "returned_at": NOW - timedelta(days=43),   "label": "Dave → Accelerate (returned)"},
        {"book": book("9780321125217"), "member": member("dave@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(40))),  "returned_at": NOW - timedelta(days=28),   "label": "Dave → Domain-Driven Design (returned)"},
        {"book": book("9781680502398"), "member": member("dave@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(25))),  "returned_at": NOW - timedelta(days=13),   "label": "Dave → Release It! (returned)"},
        # Eve (3)
        {"book": book("9780596517748"), "member": member("eve@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(35))),  "returned_at": NOW - timedelta(days=23),   "label": "Eve → JavaScript: The Good Parts (returned)"},
        {"book": book("9780201896831"), "member": member("eve@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(85))),  "returned_at": NOW - timedelta(days=73),   "label": "Eve → The Art of Computer Programming Vol. 1 (returned)"},
        {"book": book("9780132350884"), "member": member("eve@example.com"),     **dict(zip(("borrowed_at","due_date"), borrow(110))), "returned_at": NOW - timedelta(days=98),   "label": "Eve → Clean Code (returned)"},
        # Frank (3)
        {"book": book("9780596007126"), "member": member("frank@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(95))),  "returned_at": NOW - timedelta(days=83),   "label": "Frank → Head First Design Patterns (returned)"},
        {"book": book("9780135957059"), "member": member("frank@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(130))), "returned_at": NOW - timedelta(days=118),  "label": "Frank → The Pragmatic Programmer (returned)"},
        {"book": book("9780134757599"), "member": member("frank@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(60))),  "returned_at": NOW - timedelta(days=48),   "label": "Frank → Refactoring (returned)"},
        # Grace (3)
        {"book": book("9780201633610"), "member": member("grace@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(45))),  "returned_at": NOW - timedelta(days=33),   "label": "Grace → Design Patterns (returned)"},
        {"book": book("9780321146533"), "member": member("grace@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(75))),  "returned_at": NOW - timedelta(days=63),   "label": "Grace → Test-Driven Development (returned)"},
        {"book": book("9781732102200"), "member": member("grace@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(100))), "returned_at": NOW - timedelta(days=88),   "label": "Grace → A Philosophy of Software Design (returned)"},
        # Henry (3)
        {"book": book("9781491929124"), "member": member("henry@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(50))),  "returned_at": NOW - timedelta(days=38),   "label": "Henry → Site Reliability Engineering (returned)"},
        {"book": book("9781617293726"), "member": member("henry@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(65))),  "returned_at": NOW - timedelta(days=53),   "label": "Henry → Kubernetes in Action (returned)"},
        {"book": book("9781492034025"), "member": member("henry@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(80))),  "returned_at": NOW - timedelta(days=68),   "label": "Henry → Building Microservices (returned)"},
        # Iris (2)
        {"book": book("9781942788003"), "member": member("iris@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(40))),  "returned_at": NOW - timedelta(days=28),   "label": "Iris → The DevOps Handbook (returned)"},
        {"book": book("9781449373320"), "member": member("iris@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(55))),  "returned_at": NOW - timedelta(days=43),   "label": "Iris → Designing Data-Intensive Applications (returned)"},
        # Jack (2)
        {"book": book("9781492082798"), "member": member("jack@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(120))), "returned_at": NOW - timedelta(days=108),  "label": "Jack → Software Engineering at Google (returned)"},
        {"book": book("9781942788331"), "member": member("jack@example.com"),    **dict(zip(("borrowed_at","due_date"), borrow(100))), "returned_at": NOW - timedelta(days=88),   "label": "Jack → Accelerate (returned)"},
        # Karen (1)
        {"book": book("9780131177055"), "member": member("karen@example.com"),   **dict(zip(("borrowed_at","due_date"), borrow(90))),  "returned_at": NOW - timedelta(days=78),   "label": "Karen → Working Effectively with Legacy Code (returned)"},
    ]

    for b in borrows:
        _add_borrow(
            db,
            book=b["book"],
            member=b["member"],
            borrowed_at=b["borrowed_at"],
            due_date=b["due_date"],
            returned_at=b["returned_at"],
            label=b["label"],
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
