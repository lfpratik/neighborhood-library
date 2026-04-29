# Neighborhood Library API

## Project Overview
A neighborhood library management system for tracking books, members, and lending operations.
Take-home assignment for Senior Python Architect role.

## Tech Stack
- Python 3.11
- FastAPI (sync handlers — no async/await)
- SQLAlchemy 2.0 (sync, mapped_column style)
- PostgreSQL 15
- Alembic (migrations)
- Pydantic v2 (schemas)
- pytest + httpx (testing)
- Docker Compose (local dev)

## Architecture: 3-Layer + Domain Kernel

```
Request → Routes → Services → Repositories → Database
                      ↓
                   Domain (enums, exceptions, constants)
```

- **Routes** (`app/api/routes/`): HTTP concerns only. Parse request, call service, return response with correct status code.
- **Services** (`app/services/`): ALL business logic lives here. Status transitions, borrowing rules, validation.
- **Repositories** (`app/database/repositories/`): Database queries only. No business logic. Receive `Session` via DI.
- **Domain** (`app/domain/`): Pure Python. Enums, custom exceptions, constants. Zero framework imports.
- **Schemas** (`app/api/schemas/`): Pydantic v2 models for request/response. Anti-corruption layer between API and internals.

## Project Structure
```
app/
├── __init__.py
├── main.py              # FastAPI app, router includes, exception handlers
├── config.py            # Settings via pydantic-settings
├── dependencies.py      # DI: get_db, get_*_repository, get_*_service
├── domain/
│   ├── __init__.py      # Re-exports all enums, exceptions, constants
│   ├── book.py          # BookStatus enum, transitions, book exceptions
│   ├── member.py        # MemberStatus enum, transitions, member exceptions
│   └── borrow.py        # LOAN_PERIOD_DAYS, borrow exceptions
├── services/
│   ├── __init__.py
│   ├── book_service.py
│   ├── member_service.py
│   └── borrow_service.py
├── database/
│   ├── __init__.py
│   ├── session.py       # create_engine, SessionLocal
│   ├── models/
│   │   ├── __init__.py  # Base class with id, created_at, updated_at
│   │   ├── book.py
│   │   ├── member.py
│   │   └── borrow.py
│   └── repositories/
│       ├── __init__.py
│       ├── book_repository.py
│       ├── member_repository.py
│       └── borrow_repository.py
└── api/
    ├── __init__.py
    ├── schemas/
    │   ├── __init__.py
    │   ├── common.py    # PaginatedResponse, ErrorDetail
    │   ├── book.py
    │   ├── member.py
    │   └── borrow.py
    └── routes/
        ├── __init__.py
        ├── books.py
        ├── members.py
        └── borrows.py
```

## API Design (RMM Level 2)

### REST Conventions
- Resource-based URLs: `/api/v1/books`, `/api/v1/members`, `/api/v1/borrows`
- Proper HTTP verbs: GET (read), POST (create), PUT (full update), PATCH (partial/status change)
- **NO DELETE endpoints** — use status transitions instead
- Sub-resource actions for state changes: `PATCH /api/v1/books/{id}/status`

### Endpoints

#### Books
| Method | Endpoint                    | Status Codes        | Description                |
|--------|----------------------------|---------------------|----------------------------|
| POST   | /api/v1/books              | 201, 422            | Add new book               |
| GET    | /api/v1/books              | 200                 | List/search books          |
| GET    | /api/v1/books/{id}         | 200, 404            | Get book detail            |
| PUT    | /api/v1/books/{id}         | 200, 404, 422       | Full update (all fields)   |
| PATCH  | /api/v1/books/{id}         | 200, 404, 422       | Partial update (changed fields only) |
| PATCH  | /api/v1/books/{id}/status  | 200, 404, 409       | Change book status         |

#### Members
| Method | Endpoint                      | Status Codes        | Description                    |
|--------|------------------------------|---------------------|--------------------------------|
| POST   | /api/v1/members              | 201, 422            | Register member                |
| GET    | /api/v1/members              | 200                 | List/search members            |
| GET    | /api/v1/members/{id}         | 200, 404            | Get member detail              |
| PUT    | /api/v1/members/{id}         | 200, 404, 422       | Full update (all fields)       |
| PATCH  | /api/v1/members/{id}         | 200, 404, 422       | Partial update (changed fields only) |
| PATCH  | /api/v1/members/{id}/status  | 200, 404, 409       | Change member status           |

#### Borrows
| Method | Endpoint                      | Status Codes        | Description             |
|--------|------------------------------|---------------------|-------------------------|
| POST   | /api/v1/borrows              | 201, 404, 409, 422  | Borrow a book          |
| GET    | /api/v1/borrows              | 200                 | List borrows (filtered) |
| GET    | /api/v1/borrows/{id}         | 200, 404            | Get borrow detail       |
| PATCH  | /api/v1/borrows/{id}/return  | 200, 404, 409       | Return a book           |

#### System
| Method | Endpoint                      | Status Codes        | Description             |
|--------|------------------------------|---------------------|-------------------------|
| GET    | /api/v1/health               | 200                 | Health check + DB ping  |

### Query Parameters (Filtering & Pagination)
- `GET /api/v1/books?status=available&search=python&page=1&size=20`
- `GET /api/v1/members?status=active&search=john&page=1&size=20`
- `GET /api/v1/borrows?member_id=uuid&book_id=uuid&active=true&overdue=true&page=1&size=20`

### Pagination Response Format
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

### Error Response Format
```json
{
  "detail": {
    "code": "BOOK_NOT_AVAILABLE",
    "message": "Book is currently borrowed by another member"
  }
}
```

---

## Data Model — Entity Definitions

### Books Table (`books`)
| Column           | Type         | Constraints                         | Notes                    |
|------------------|--------------|-------------------------------------|--------------------------|
| id               | UUID         | PK, default uuid7                   | Time-sortable            |
| title            | String(255)  | NOT NULL                            |                          |
| author           | String(255)  | NOT NULL                            |                          |
| isbn             | String(13)   | NULLABLE, UNIQUE                    | Optional for donated books|
| publisher        | String(255)  | NULLABLE                            |                          |
| publication_year | Integer      | NULLABLE                            |                          |
| genre            | String(100)  | NULLABLE                            |                          |
| status           | String(20)   | NOT NULL, default "available"       | See BookStatus enum      |
| created_at       | DateTime(tz) | NOT NULL, server default now()      |                          |
| updated_at       | DateTime(tz) | NOT NULL, server default now(), onupdate now() |               |

### Members Table (`members`)
| Column           | Type         | Constraints                         | Notes                    |
|------------------|--------------|-------------------------------------|--------------------------|
| id               | UUID         | PK, default uuid7                   | Time-sortable            |
| name             | String(255)  | NOT NULL                            |                          |
| email            | String(255)  | NOT NULL, UNIQUE                    | Used for lookup          |
| phone            | String(20)   | NULLABLE                            |                          |
| address          | Text         | NULLABLE                            |                          |
| status           | String(20)   | NOT NULL, default "active"          | See MemberStatus enum    |
| created_at       | DateTime(tz) | NOT NULL, server default now()      |                          |
| updated_at       | DateTime(tz) | NOT NULL, server default now(), onupdate now() |               |

### Borrows Table (`borrows`)
| Column           | Type         | Constraints                         | Notes                    |
|------------------|--------------|-------------------------------------|--------------------------|
| id               | UUID         | PK, default uuid7                   | Time-sortable            |
| book_id          | UUID         | FK → books.id, NOT NULL, INDEX      |                          |
| member_id        | UUID         | FK → members.id, NOT NULL, INDEX    |                          |
| borrowed_at      | DateTime(tz) | NOT NULL, default now()             |                          |
| due_date         | DateTime(tz) | NOT NULL                            | borrowed_at + 14 days    |
| returned_at      | DateTime(tz) | NULLABLE                            | NULL = active borrow     |
| notes            | Text         | NULLABLE                            |                          |
| created_at       | DateTime(tz) | NOT NULL, server default now()      |                          |

### Relationships
- `Book.borrows` → one-to-many → `Borrow` (back_populates="book")
- `Member.borrows` → one-to-many → `Borrow` (back_populates="member")
- `Borrow.book` → many-to-one → `Book` (back_populates="borrows")
- `Borrow.member` → many-to-one → `Member` (back_populates="borrows")

### Database Indexes
- `ix_books_status` on books(status) — filter available books
- `ix_members_email` UNIQUE on members(email) — lookup + constraint
- `ix_borrows_book_active` on borrows(book_id, returned_at) — "is this book currently borrowed?"
- `ix_borrows_member_active` on borrows(member_id, returned_at) — "what does this member have out?"
- `ix_borrows_due_date` on borrows(due_date) — overdue query

### Schema Design Checklist (Maps to Evaluation Criteria #1)
- ✅ Normalized: No redundant data. Borrow references book_id and member_id via FK.
- ✅ Proper relationships: FK constraints with referential integrity.
- ✅ Indexes on query patterns: status filters, active borrow lookups, overdue scans.
- ✅ Timestamps with timezone: All datetime columns use DateTime(timezone=True).
- ✅ UUID primary keys: Distributed-safe, time-sortable via uuid7.
- ✅ Soft lifecycle: No deletes — status fields manage entity lifecycle.
- ✅ Audit trail: created_at on all tables, updated_at on mutable tables (books, members).
- ✅ Unique constraints: email on members, isbn on books (nullable unique).
- ✅ NULL semantics: returned_at NULL means active borrow — clean, queryable.
- ✅ No updated_at on borrows: Borrow records are append-only (created, then returned). No edits.

---

## Domain Layer — Per-Entity Files (Pure Python, Zero Framework Imports)

### app/domain/book.py
```python
from enum import Enum

class BookStatus(str, Enum):
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
            raise BookNotAvailableError(f"Book is retired and cannot change status")
        if current == BookStatus.BORROWED and new == BookStatus.RETIRED:
            raise BookRetirementError(f"Book must be returned before retiring")
        raise BookNotAvailableError(f"Cannot transition from '{current.value}' to '{new.value}'")
```

### app/domain/member.py
```python
from enum import Enum

class MemberStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

MEMBER_STATUS_TRANSITIONS = {
    MemberStatus.ACTIVE: [MemberStatus.INACTIVE, MemberStatus.SUSPENDED],
    MemberStatus.INACTIVE: [MemberStatus.ACTIVE],
    MemberStatus.SUSPENDED: [MemberStatus.ACTIVE],
}

class MemberNotFoundError(Exception):
    """Member with given ID does not exist."""

class MemberNotActiveError(Exception):
    """Member is not active and cannot borrow books."""

def validate_member_status_transition(current: MemberStatus, new: MemberStatus) -> None:
    """Validate that a member status transition is allowed. Raises on invalid."""
    allowed = MEMBER_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed:
        raise MemberNotActiveError(f"Cannot transition from '{current.value}' to '{new.value}'")
```

### app/domain/borrow.py
```python
from datetime import datetime, timedelta, timezone

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
    return datetime.now(timezone.utc) > due_date

def validate_borrow_is_active(returned_at: datetime | None) -> None:
    """Validate that a borrow has not already been returned. Raises on invalid."""
    if returned_at is not None:
        raise BookAlreadyReturnedError("This book has already been returned")
```

### app/domain/__init__.py
```python
from app.domain.book import BookStatus, BOOK_STATUS_TRANSITIONS
from app.domain.book import BookNotFoundError, BookNotAvailableError, BookRetirementError
from app.domain.book import validate_book_status_transition
from app.domain.member import MemberStatus, MEMBER_STATUS_TRANSITIONS
from app.domain.member import MemberNotFoundError, MemberNotActiveError
from app.domain.member import validate_member_status_transition
from app.domain.borrow import LOAN_PERIOD_DAYS, calculate_due_date, is_overdue
from app.domain.borrow import BorrowNotFoundError, BookAlreadyBorrowedError, BookAlreadyReturnedError
from app.domain.borrow import validate_borrow_is_active
```

---

## Status Lifecycles

### Book Status
```
available → borrowed    (via POST /api/v1/borrows)
borrowed  → available   (via PATCH /api/v1/borrows/{id}/return)
available → retired     (via PATCH /api/v1/books/{id}/status)
retired   → (terminal)  (no transitions out)
```
- Cannot borrow a `borrowed` or `retired` book → 409
- Cannot retire a `borrowed` book (must be returned first) → 409

### Member Status
```
active    → inactive    (via PATCH /api/v1/members/{id}/status)
active    → suspended   (via PATCH /api/v1/members/{id}/status)
inactive  → active      (via PATCH /api/v1/members/{id}/status)
suspended → active      (via PATCH /api/v1/members/{id}/status)
```
- Only `active` members can borrow books → 409
- Suspending/deactivating does NOT auto-return their books

### Borrow Rules
- A book can only have ONE active borrow (returned_at IS NULL)
- Only `active` members can borrow
- Only `available` books can be borrowed
- `due_date` = `borrowed_at` + 14 days
- Returning sets `returned_at = now()` and flips book.status to `available`
- Cannot return an already-returned borrow → 409
- Overdue = `due_date < now() AND returned_at IS NULL`

---

## Optional Features (Future Enhancements)

### Fines / Penalty System (Optional)

#### Fines Table (`fines`)
| Column     | Type          | Constraints                    | Notes                    |
|------------|---------------|--------------------------------|--------------------------|
| id         | UUID          | PK, default uuid7              |                          |
| borrow_id  | UUID          | FK → borrows.id, NOT NULL      | Which borrow caused it   |
| amount     | Decimal(10,2) | NOT NULL                       | Calculated fine amount   |
| reason     | String(255)   | NOT NULL                       | e.g. "Overdue: 5 days"  |
| paid_at    | DateTime(tz)  | NULLABLE                       | NULL = unpaid            |
| created_at | DateTime(tz)  | NOT NULL, server default now() |                          |

#### Domain: app/domain/fine.py
```python
from decimal import Decimal

DAILY_FINE_RATE = Decimal("0.50")  # $0.50 per day overdue

class FineNotFoundError(Exception): ...
class FineAlreadyPaidError(Exception): ...

def calculate_fine(due_date: datetime, returned_at: datetime) -> Decimal:
    """Calculate fine amount based on overdue days."""
    if returned_at <= due_date:
        return Decimal("0.00")
    overdue_days = (returned_at - due_date).days
    return Decimal(str(overdue_days)) * DAILY_FINE_RATE
```

#### Endpoints
| Method | Endpoint                         | Status Codes   | Description              |
|--------|----------------------------------|----------------|--------------------------|
| GET    | /api/v1/members/{id}/fines       | 200, 404       | List fines for a member  |
| GET    | /api/v1/fines/{id}               | 200, 404       | Get fine detail          |
| PATCH  | /api/v1/fines/{id}/pay           | 200, 404, 409  | Mark fine as paid        |

#### Integration
- `borrow_service.return_book()` calculates fine if overdue and auto-creates a fine record
- Fine amount shown on borrow detail page and member detail page
- Requires: FineRepository, FineService, fine schemas, fine routes
- No existing code changes — purely additive

### Reservations / Hold System (Optional)

#### Book Status Addition
```python
class BookStatus(str, Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"    # NEW
    RETIRED = "retired"
```

#### Reservations Table (`reservations`)
| Column       | Type         | Constraints                    | Notes                        |
|--------------|--------------|--------------------------------|------------------------------|
| id           | UUID         | PK, default uuid7              |                              |
| book_id      | UUID         | FK → books.id, NOT NULL        |                              |
| member_id    | UUID         | FK → members.id, NOT NULL      |                              |
| reserved_at  | DateTime(tz) | NOT NULL, default now()        |                              |
| expires_at   | DateTime(tz) | NOT NULL                       | reserved_at + 3 days         |
| fulfilled_at | DateTime(tz) | NULLABLE                       | NULL = not yet picked up     |
| cancelled_at | DateTime(tz) | NULLABLE                       | NULL = not cancelled         |
| created_at   | DateTime(tz) | NOT NULL, server default now() |                              |

#### Domain Rules
```
available → reserved    (via POST /api/v1/reservations)
reserved  → borrowed    (when reserving member picks up the book)
reserved  → available   (when reservation expires or is cancelled)
```
- `HOLD_PERIOD_DAYS = 3`
- Only `active` members can reserve
- Only `available` books can be reserved
- When borrowing a reserved book, verify borrowing member matches the reservation
- Background job needed: expire reservations past `expires_at`

#### Endpoints
| Method | Endpoint                              | Description                  |
|--------|---------------------------------------|------------------------------|
| POST   | /api/v1/reservations                  | Reserve a book               |
| GET    | /api/v1/reservations                  | List reservations (filtered) |
| PATCH  | /api/v1/reservations/{id}/cancel      | Cancel a reservation         |

---

## Coding Conventions

### Python
- Type hints on all function signatures and return types
- Docstrings on all service methods (one-line summary)
- Use `uuid_utils.uuid7()` for all primary keys (time-sortable UUIDs)
- **Sync everywhere**: plain `def`, no `async/await`
- Import style: stdlib → third-party → local (isort compatible)

### SQLAlchemy (Sync)
- Use `mapped_column()` style (SQLAlchemy 2.0)
- Use `Mapped[type]` annotations
- `create_engine()` (NOT create_async_engine)
- `sessionmaker` → `SessionLocal` (NOT async_sessionmaker)
- `Session` type hint (NOT AsyncSession)
- Base class in `database/models/__init__.py` with id, created_at
- Books and Members also get `updated_at` column
- Status fields: `String` column, validated against domain Enum in service layer
- Timestamps: `func.now()` for server defaults, `onupdate=func.now()` for updated_at
- Use `relationship()` with `back_populates` (NOT backref)
- Use `joinedload()` or `selectinload()` for eager loading in repositories

### Pydantic
- Use `model_config = ConfigDict(...)` (v2 style, NOT inner Config class)
- Separate schemas per entity: `{Entity}Create`, `{Entity}Update`, `{Entity}Response`, `{Entity}StatusUpdate`
- Use `from_attributes = True` for ORM mode
- Common schemas in `api/schemas/common.py`: PaginatedResponse, ErrorDetail

### FastAPI
- Each route file creates its own `APIRouter(tags=["..."])`
- Routers mounted in `main.py` with prefix `/api/v1`
- Dependencies via `Depends()` — never instantiate services/repos directly in routes
- Use `status_code=status.HTTP_201_CREATED` for POST endpoints
- Use `Response` header `Location` for created resources

### Error Handling
- Each entity has its own exceptions in `domain/{entity}.py`
- Register global exception handlers in `main.py`:
  - *NotFoundError → HTTPException(404)
  - *NotAvailableError, *AlreadyBorrowedError, *RetirementError, *AlreadyReturnedError → HTTPException(409)
  - *NotActiveError → HTTPException(409)
  - Pydantic ValidationError → 422 (automatic via FastAPI)

### Testing (Sync)
- pytest (plain, NO pytest-asyncio)
- `TestClient` from FastAPI (sync, NOT AsyncClient)
- Override `get_db` dependency with test database session
- Test files: `test_domain.py`, `test_services.py`, `test_api.py`
- Focus on: invalid borrows, status transitions, edge cases, overdue detection

---

## Docker & Dev Setup
- `docker-compose.yml`: PostgreSQL 15 + FastAPI app with backend healthcheck
- `devbox.json`: provisions Python 3.11, activates venv, installs deps on `devbox shell`
- `Makefile` targets: `demo`, `dev`, `run`, `build`, `up`, `down`, `logs`, `test`, `seed`, `migrate`, `lint`, `lint-fix`, `format`, `typecheck`
- `.env.example` with DATABASE_URL, APP_HOST, APP_PORT
- `.env.local` (local dev, auto-created by `make install`) — uses `localhost` DB host
- `.env.docker` (Docker, auto-created by `make demo`) — uses `db` Docker service host
- `make demo` = build + start + migrate + seed (one command for evaluator)
- `make dev` = local uvicorn server with --reload (requires local Postgres + .env.local)
- `make run` = `docker-compose up -d` (start Docker services)

## Seed Data (scripts/seed.py)
- 5 books: 3 available, 1 borrowed, 1 retired
- 3 members: 1 active, 1 inactive, 1 suspended
- 2 active borrows: 1 normal (due in future), 1 overdue (due in past)
- 1 completed borrow (returned_at set)
- Idempotent: checks existence before inserting (safe to run multiple times)

---

## File Naming
- Models: `app/database/models/book.py` → class `Book`
- Repos: `app/database/repositories/book_repository.py` → class `BookRepository`
- Services: `app/services/book_service.py` → class `BookService`
- Schemas: `app/api/schemas/book.py` → `BookCreate`, `BookUpdate`, `BookResponse`, `BookStatusUpdate`
- Routes: `app/api/routes/books.py` → `router` variable
- Domain: `app/domain/book.py` → `BookStatus`, `BOOK_STATUS_TRANSITIONS`, exceptions

## Key Patterns

### Database Session (Sync)
```python
# database/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
```

### Dependency Chain (Sync)
```python
# dependencies.py
from typing import Generator
from sqlalchemy.orm import Session

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_book_repository(db: Session = Depends(get_db)) -> BookRepository:
    return BookRepository(db)

def get_book_service(repo: BookRepository = Depends(get_book_repository)) -> BookService:
    return BookService(repo)
```

### Service Method Pattern (Sync) — Services call domain validators
```python
# services/book_service.py
from app.domain.book import BookStatus, validate_book_status_transition, BookNotFoundError

def update_status(self, book_id: UUID, new_status: BookStatus) -> Book:
    """Change book status. Domain layer validates the transition."""
    book = self.repo.get_by_id(book_id)
    if not book:
        raise BookNotFoundError(f"Book {book_id} not found")
    validate_book_status_transition(BookStatus(book.status), new_status)
    return self.repo.update_status(book_id, new_status.value)

# services/borrow_service.py
from app.domain.borrow import calculate_due_date, validate_borrow_is_active
from app.domain.book import BookStatus, BookNotAvailableError, BookNotFoundError
from app.domain.member import MemberStatus, MemberNotActiveError, MemberNotFoundError

def borrow_book(self, book_id: UUID, member_id: UUID) -> Borrow:
    """Record a book borrow. Domain layer validates all rules."""
    book = self.book_repo.get_by_id(book_id)
    if not book:
        raise BookNotFoundError(f"Book {book_id} not found")
    if book.status != BookStatus.AVAILABLE.value:
        raise BookNotAvailableError(f"Book is currently {book.status}")
    member = self.member_repo.get_by_id(member_id)
    if not member:
        raise MemberNotFoundError(f"Member {member_id} not found")
    if member.status != MemberStatus.ACTIVE.value:
        raise MemberNotActiveError(f"Member is {member.status}")
    due_date = calculate_due_date(datetime.now(timezone.utc))
    # ... create borrow, update book status to borrowed

def return_book(self, borrow_id: UUID) -> Borrow:
    """Return a borrowed book. Domain layer validates it's still active."""
    borrow = self.borrow_repo.get_by_id(borrow_id)
    if not borrow:
        raise BorrowNotFoundError(f"Borrow {borrow_id} not found")
    validate_borrow_is_active(borrow.returned_at)
    # ... set returned_at, update book status to available
```

### Route Pattern (Sync)
```python
@router.post("", status_code=status.HTTP_201_CREATED)
def create_book(
    data: BookCreate,
    service: BookService = Depends(get_book_service),
) -> BookResponse:
    """Add a new book to the library."""
    book = service.create_book(data)
    return BookResponse.model_validate(book)
```

### Base Model Pattern
```python
# database/models/__init__.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid_utils

class Base(DeclarativeBase):
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid_utils.uuid7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

---

## Frontend — Next.js App

### Tech Stack
- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Lucide React (icons)

### Design Direction
- **Tone**: Clean, professional, library-warm — not generic SaaS
- **Color palette**: Warm neutrals (stone/amber) with green/amber/red status accents
- **Typography**: Use `font-sans` (system stack) for body, keep it readable
- **Layout**: Sidebar navigation + content area, desktop-first
- **Character**: Subtle book/library warmth — not clinical, not playful

### Frontend Structure
```
frontend/
├── package.json
├── next.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.mjs
├── Dockerfile
├── .env.example               # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
├── devbox.json                # Node.js 20
│
└── src/
    ├── app/
    │   ├── layout.tsx          # Root layout with Sidebar
    │   ├── page.tsx            # Dashboard
    │   ├── books/
    │   │   ├── page.tsx        # Books list
    │   │   └── [id]/
    │   │       └── page.tsx    # Book detail (view + edit)
    │   ├── members/
    │   │   ├── page.tsx        # Members list
    │   │   └── [id]/
    │   │       └── page.tsx    # Member detail (view + edit)
    │   └── borrows/
    │       ├── page.tsx        # Borrows list
    │       └── [id]/
    │           └── page.tsx    # Borrow detail (read-only)
    │
    ├── components/
    │   ├── layout/
    │   │   └── Sidebar.tsx     # Navigation sidebar
    │   ├── shared/
    │   │   ├── DetailField.tsx # Reusable label-value display
    │   │   └── BackLink.tsx    # Reusable "← Back to X" link
    │   ├── books/
    │   │   ├── BookTable.tsx
    │   │   └── BookFormModal.tsx
    │   ├── members/
    │   │   ├── MemberTable.tsx
    │   │   └── MemberFormModal.tsx
    │   └── borrows/
    │       ├── BorrowTable.tsx
    │       └── BorrowFormModal.tsx
    │
    ├── lib/
    │   ├── api.ts              # Typed fetch wrapper
    │   └── utils.ts            # Date formatting, status colors
    │
    └── types/
        └── index.ts            # Matches backend Pydantic schemas
```

### TypeScript Types (Must Match Backend Schemas)
```typescript
// types/index.ts
export interface Book {
  id: string;
  title: string;
  author: string;
  isbn: string | null;
  publisher: string | null;
  publication_year: number | null;
  genre: string | null;
  status: "available" | "borrowed" | "retired";
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  address: string | null;
  status: "active" | "inactive" | "suspended";
  created_at: string;
  updated_at: string;
}

export interface Borrow {
  id: string;
  book_id: string;
  member_id: string;
  borrowed_at: string;
  due_date: string;
  returned_at: string | null;
  notes: string | null;
  created_at: string;
  book: Book;
  member: Member;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
```

### API Client Pattern
```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.message || `API error: ${res.status}`);
  }
  return res.json();
}

// Functions to export:
// Books:   getBooks(params?), getBook(id), createBook(data), patchBook(id, data), updateBookStatus(id, status)
// Members: getMembers(params?), getMember(id), createMember(data), patchMember(id, data), updateMemberStatus(id, status)
// Borrows: getBorrows(params?), getBorrow(id), createBorrow(data), returnBorrow(id)
//
// patchBook uses PATCH /books/{id} with only changed fields (partial update)
// patchMember uses PATCH /members/{id} with only changed fields (partial update)
// Frontend detail page edit mode uses PATCH (not PUT) — sends only modified fields
```

### Status Badge Colors
```
Books:    available → green    | borrowed → amber    | retired → gray
Members:  active → green       | inactive → gray     | suspended → red
Borrows:  active → blue        | overdue → red       | returned → green
```

### Pages Overview

#### Dashboard (`/`)
- 3 stat cards: Total Books, Active Members, Active Borrows
- Overdue borrows alert (count + link to borrows page with overdue filter)
- Recent activity: last 5 borrows

#### Books (`/books`)
- Table: title (links to /books/{id}), author, isbn, genre, status badge, actions
- Search bar (filters title/author)
- Status filter dropdown (all/available/borrowed/retired)
- "Add Book" button → opens modal with BookCreate form
- Per-row actions: "Retire" button (only on available books)

#### Members (`/members`)
- Table: name (links to /members/{id}), email, phone, status badge, actions
- Search bar (filters name/email)
- Status filter dropdown
- "Add Member" button → modal
- Per-row actions: Suspend/Activate/Deactivate buttons based on current status

#### Borrows (`/borrows`)
- Table: book title (links to /books/{id}), member name (links to /members/{id}), borrowed date, due date, status, actions
- Filter tabs: All / Active / Overdue / Returned
- "Borrow Book" button → modal (dropdown to select available book + active member)
- Per-row "Return" button (only on active borrows)
- Per-row "View" button/icon → /borrows/{id}
- Overdue rows highlighted with red/amber background

#### Book Detail (`/books/[id]`) — View + Edit
- **View mode** (default): label-value card showing all book fields + status badge + dates
- **Edit mode** (toggle via "Edit" button): fields become editable inputs, "Save" + "Cancel" buttons
- Editable: title, author, isbn, publisher, publication_year, genre
- NOT editable: status (use action buttons), id, dates
- Save uses **PATCH** (not PUT): sends only changed fields via `patchBook(id, changedFields)`
- Status action: "Retire Book" button (only when available)
- Borrow History section: table of all borrows for this book (fetched from GET /borrows?book_id={id})
- 404 handling: show "Book not found" with back link

#### Member Detail (`/members/[id]`) — View + Edit
- Same view/edit toggle pattern as Book Detail
- Editable: name, email, phone, address
- NOT editable: status, id, dates
- Save uses **PATCH** (not PUT): sends only changed fields via `patchMember(id, changedFields)`
- Status actions: Suspend/Deactivate (when active), Activate (when inactive/suspended)
- Active Borrows section: current borrows for this member (GET /borrows?member_id={id}&active=true)
- Full Borrow History section: all borrows (GET /borrows?member_id={id})

#### Borrow Detail (`/borrows/[id]`) — Read-Only
- Full details card: book info (link to /books/{id}), member info (link to /members/{id})
- Dates: borrowed_at, due_date, returned_at (or "Not yet returned")
- Notes field
- Status badge: Active / Overdue / Returned
- Overdue alert: "This book is X days overdue" banner if overdue
- "Return Book" button if active/overdue
- No edit mode — borrows are append-only

#### Shared Components
- **DetailField**: reusable label-value pair display (label in muted small text, value below)
- **BackLink**: reusable "← Back to {page}" navigation link with ArrowLeft icon

#### List Page Navigation
- BookTable: title column links to /books/{id}
- MemberTable: name column links to /members/{id}
- BorrowTable: book title links to /books/{book_id}, member name links to /members/{member_id}, "View" button links to /borrows/{id}

### Frontend Conventions
- Use `"use client"` directive on pages/components that use hooks (useState, useEffect)
- All API calls in useEffect or event handlers, never in server components for this project
- Show loading states (skeleton or spinner) while fetching
- Show toast/alert on success/error after mutations (create, return, status change)
- All forms validate required fields before submitting
- After mutation, refetch the list to show updated data
- Use `encodeURIComponent` for search params

### Docker Setup (Frontend)
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### Devbox (Frontend)
```json
{
  "packages": ["nodejs@20"],
  "shell": {
    "init_hook": [
      "if [ ! -d node_modules ]; then npm install; fi",
      "echo 'Frontend ready: npm run dev'"
    ]
  }
}
```
