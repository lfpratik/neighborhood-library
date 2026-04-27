# Neighborhood Library — Claude Code Prompts

## How to Use
1. Place `CLAUDE.md` and `.claude/` folder in your project root
2. Open Claude Code in the project directory
3. **Backend first:** Run Prompts 1 → 7 in order
4. **Frontend second:** Run Prompts F1 → F6 in order (backend must be running)
5. Use `/clear` between phases and where noted to manage context
6. Verify each step works before moving to the next

---

# Part 1 — Backend Prompts (Python/FastAPI)

---

## Prompt 1 — Project Scaffold + Domain Layer + Database Setup

> This is the longest prompt. It creates everything needed for the app to boot.

```
Read CLAUDE.md thoroughly. Then scaffold the entire project:

1. CREATE ALL FOLDERS AND __init__.py FILES matching the Project Structure in CLAUDE.md. Every directory under app/ needs an __init__.py.

2. CREATE config files at project root:
   - requirements.txt: fastapi, uvicorn, sqlalchemy, psycopg2-binary, alembic, pydantic, pydantic-settings, uuid-utils, python-dotenv, pytest, httpx
   - .env.example: DATABASE_URL=postgresql://library:library@localhost:5432/library_db, APP_HOST=0.0.0.0, APP_PORT=8000
   - .gitignore: standard Python + .env + __pycache__ + .pytest_cache + alembic/versions/*.pyc
   - pyproject.toml: project metadata, ruff config, pytest config
   - docker-compose.yml: PostgreSQL 16 service (library:library@db:5432/library_db) + app service (build context, depends_on db, env_file, port 8000)
   - Dockerfile: Python 3.12-slim, WORKDIR /app, copy requirements, pip install, copy source, CMD uvicorn
   - Makefile with targets: setup (docker-compose build + migrate + seed), run (docker-compose up), test (pytest), migrate (alembic upgrade head), seed (python scripts/seed.py), lint (ruff check), down (docker-compose down)

3. CREATE app/config.py:
   - Use pydantic-settings BaseSettings
   - Fields: database_url (str), app_host (str, default "0.0.0.0"), app_port (int, default 8000)
   - model_config with env_file=".env"

4. CREATE app/database/session.py:
   - Follow the "Database Session (Sync)" pattern in CLAUDE.md exactly
   - create_engine + sessionmaker → SessionLocal

5. CREATE app/database/models/__init__.py:
   - Follow the "Base Model Pattern" in CLAUDE.md exactly
   - Base class with id (UUID, uuid7) and created_at (DateTime timezone)

6. CREATE the domain layer — all 3 files exactly as specified in CLAUDE.md under "Domain Layer — Per-Entity Files":
   - app/domain/book.py (BookStatus, BOOK_STATUS_TRANSITIONS, exceptions, validate_book_status_transition)
   - app/domain/member.py (MemberStatus, MEMBER_STATUS_TRANSITIONS, exceptions, validate_member_status_transition)
   - app/domain/borrow.py (LOAN_PERIOD_DAYS, exceptions, calculate_due_date, is_overdue, validate_borrow_is_active)
   - app/domain/__init__.py (re-export everything)

7. CREATE app/main.py:
   - FastAPI app with title="Neighborhood Library API", version="1.0.0"
   - Health check endpoint: GET /api/v1/health that pings the database
   - Register global exception handlers for all domain exceptions (map to 404, 409 as specified in CLAUDE.md "Error Handling")
   - Router includes will be added later (just comment placeholders for now)

8. CREATE app/dependencies.py:
   - Follow the "Dependency Chain (Sync)" pattern in CLAUDE.md
   - get_db generator only for now (service/repo deps added later)

9. INITIALIZE Alembic:
   - alembic.ini pointing to migrations/
   - migrations/env.py configured to use app.config.settings.database_url and app.database.models.Base.metadata

Verify: The app should start with `uvicorn app.main:app --reload` (will fail on DB connection without PostgreSQL, but no import errors).
```

---

## Prompt 2 — Database Models (All 3 Entities)

```
Read CLAUDE.md "Data Model — Entity Definitions" for exact columns, types, and constraints.
Read app/domain/ files for status enums.

Create all 3 SQLAlchemy models in one go:

1. app/database/models/book.py — class Book(Base):
   - __tablename__ = "books"
   - All columns from CLAUDE.md "Books Table" using Mapped[] + mapped_column()
   - updated_at column with onupdate=func.now()
   - status defaults to BookStatus.AVAILABLE.value
   - relationship: borrows = relationship("Borrow", back_populates="book")
   - Index on status column

2. app/database/models/member.py — class Member(Base):
   - __tablename__ = "members"
   - All columns from CLAUDE.md "Members Table"
   - updated_at column with onupdate=func.now()
   - status defaults to MemberStatus.ACTIVE.value
   - email has unique=True
   - relationship: borrows = relationship("Borrow", back_populates="member")

3. app/database/models/borrow.py — class Borrow(Base):
   - __tablename__ = "borrows"
   - All columns from CLAUDE.md "Borrows Table"
   - NO updated_at (append-only)
   - ForeignKey to books.id and members.id
   - relationships: book = relationship("Book", back_populates="borrows"), member = relationship("Member", back_populates="borrows")
   - Composite indexes from CLAUDE.md "Database Indexes"

4. Update app/database/models/__init__.py — import all 3 models so Alembic discovers them.

5. Generate the initial Alembic migration:
   - Run: alembic revision --autogenerate -m "initial_schema"
   - Verify the generated migration creates all 3 tables with correct columns, constraints, and indexes.
```

---

## Prompt 3 — Repositories + Schemas

```
Create repositories and Pydantic schemas for all 3 entities.

REPOSITORIES — Read CLAUDE.md "Query Parameters" for filters each repo needs:

1. app/database/repositories/book_repository.py — class BookRepository:
   - __init__(self, db: Session)
   - get_by_id(book_id: UUID) -> Book | None
   - get_all(page, size, status: str | None, search: str | None) -> tuple[list[Book], int]
     - search filters on title and author (ILIKE)
     - status filters on book.status
     - returns (items, total_count) for pagination
   - create(data) -> Book
   - update(book_id, data) -> Book
   - update_status(book_id, new_status: str) -> Book

2. app/database/repositories/member_repository.py — class MemberRepository:
   - Same pattern as BookRepository
   - search filters on name and email
   - get_by_email(email: str) for duplicate checking

3. app/database/repositories/borrow_repository.py — class BorrowRepository:
   - get_by_id(borrow_id) with joinedload on book and member relationships
   - get_all(page, size, member_id, book_id, active: bool, overdue: bool) -> tuple[list[Borrow], int]
     - active=true filters returned_at IS NULL
     - overdue=true filters due_date < now() AND returned_at IS NULL
   - get_active_by_book_id(book_id) -> Borrow | None (for checking if book is currently borrowed)
   - create(data) -> Borrow
   - update_returned_at(borrow_id, returned_at) -> Borrow

SCHEMAS — Read CLAUDE.md entity tables for fields:

4. app/api/schemas/common.py:
   - PaginatedResponse (generic, with items: list, total: int, page: int, size: int, pages: int)
   - ErrorDetail (code: str, message: str)

5. app/api/schemas/book.py:
   - BookCreate: title (required), author (required), isbn, publisher, publication_year, genre
   - BookUpdate: all fields optional
   - BookStatusUpdate: status (BookStatus enum)
   - BookResponse: all fields including id, status, created_at, updated_at. Use ConfigDict(from_attributes=True)

6. app/api/schemas/member.py:
   - Same pattern: MemberCreate, MemberUpdate, MemberStatusUpdate, MemberResponse

7. app/api/schemas/borrow.py:
   - BorrowCreate: book_id (UUID), member_id (UUID), notes (optional)
   - BorrowResponse: all fields + nested BookResponse and MemberResponse for the relationships. Use ConfigDict(from_attributes=True)
```

---

## Prompt 4 — Service Layer (Business Logic)

```
Create all 3 service classes. Read CLAUDE.md "Status Lifecycles", "Borrow Rules", and "Service Method Pattern" for exact logic.

Services MUST call domain validation functions — never inline the rules.

1. app/services/book_service.py — class BookService:
   - __init__(self, repo: BookRepository)
   - create_book(data: BookCreate) -> Book
   - get_book(book_id) -> Book (raise BookNotFoundError if not found)
   - list_books(page, size, status, search) -> tuple[list[Book], int]
   - update_book(book_id, data: BookUpdate) -> Book
   - update_status(book_id, data: BookStatusUpdate) -> Book
     - Call validate_book_status_transition() from domain/book.py
     - Special case: if transitioning to RETIRED and book is BORROWED, raise BookRetirementError

2. app/services/member_service.py — class MemberService:
   - Same CRUD pattern as BookService
   - update_status calls validate_member_status_transition() from domain/member.py
   - create_member checks for duplicate email via repo.get_by_email()

3. app/services/borrow_service.py — class BorrowService:
   - __init__(self, borrow_repo, book_repo, member_repo) — needs all 3 repos
   - borrow_book(data: BorrowCreate) -> Borrow
     - Validate book exists (BookNotFoundError)
     - Validate book.status == "available" (BookNotAvailableError)
     - Validate member exists (MemberNotFoundError)
     - Validate member.status == "active" (MemberNotActiveError)
     - Check no active borrow for this book via repo.get_active_by_book_id() (BookAlreadyBorrowedError)
     - Calculate due_date using calculate_due_date() from domain/borrow.py
     - Create borrow record
     - Update book status to "borrowed"
     - Commit transaction (db.commit)
   - return_book(borrow_id) -> Borrow
     - Validate borrow exists
     - Call validate_borrow_is_active() from domain/borrow.py
     - Set returned_at = now()
     - Update book status back to "available"
     - Commit transaction
   - get_borrow(borrow_id) -> Borrow
   - list_borrows(page, size, member_id, book_id, active, overdue) -> tuple[list[Borrow], int]

4. Update app/dependencies.py:
   - Add get_*_repository and get_*_service dependency functions for all 3 entities
   - BorrowService gets all 3 repos injected (follow Dependency Chain pattern in CLAUDE.md)
```

---

## Prompt 5 — API Routes

```
Create all route files. Read CLAUDE.md "Endpoints" table for exact methods, paths, and status codes.

Follow the "Route Pattern (Sync)" in CLAUDE.md. All routes use Depends() for service injection.

1. app/api/routes/books.py:
   - router = APIRouter(prefix="/books", tags=["Books"])
   - POST "" → 201 + Location header
   - GET "" → 200, query params: status, search, page, size
   - GET "/{book_id}" → 200 or 404
   - PUT "/{book_id}" → 200 or 404
   - PATCH "/{book_id}/status" → 200 or 409
   - All handlers return BookResponse or PaginatedResponse

2. app/api/routes/members.py:
   - Same pattern as books
   - router = APIRouter(prefix="/members", tags=["Members"])

3. app/api/routes/borrows.py:
   - router = APIRouter(prefix="/borrows", tags=["Borrows"])
   - POST "" → 201 (borrow a book)
   - GET "" → 200, query params: member_id, book_id, active, overdue, page, size
   - GET "/{borrow_id}" → 200 or 404
   - PATCH "/{borrow_id}/return" → 200 or 409

4. Update app/main.py:
   - Import all 3 routers
   - app.include_router(books.router, prefix="/api/v1")
   - app.include_router(members.router, prefix="/api/v1")
   - app.include_router(borrows.router, prefix="/api/v1")

5. Verify: Start the app, visit /docs — all endpoints should appear in Swagger UI with correct tags, methods, and schemas.
```

---

## Prompt 6 — Seed Data + Makefile Wiring + Documentation

```
Create seed script and finalize all project documentation.

1. CREATE scripts/seed.py:
   - Idempotent (check if data exists before inserting)
   - Import models and SessionLocal
   - Seed data as specified in CLAUDE.md "Seed Data":
     - 5 books:
       - "Clean Code" by Robert Martin (available)
       - "Design Patterns" by Gang of Four (available)
       - "The Pragmatic Programmer" by Hunt & Thomas (available)
       - "Refactoring" by Martin Fowler (borrowed — will have an active borrow)
       - "Mythical Man Month" by Fred Brooks (retired)
     - 3 members:
       - "Alice Johnson" alice@example.com (active)
       - "Bob Smith" bob@example.com (inactive)
       - "Charlie Brown" charlie@example.com (suspended)
     - 3 borrow records:
       - Alice borrowed "Refactoring" 5 days ago (active, due in 9 days — normal)
       - Alice borrowed "Clean Code" 30 days ago and returned it 20 days ago (completed)
       - Alice borrowed "Design Patterns" 20 days ago (active, due 6 days ago — OVERDUE)
     - Make sure book statuses match: "Refactoring" and "Design Patterns" should be status="borrowed"
   - Run via: python -m scripts.seed or python scripts/seed.py

2. VERIFY Makefile targets work:
   - make setup: docker-compose build, alembic upgrade head, python scripts/seed.py
   - make run: docker-compose up
   - make test: pytest
   - make seed: python scripts/seed.py
   - make migrate: alembic upgrade head
   - make down: docker-compose down -v

3. CREATE README.md:
   - Project title and one-line description
   - Tech stack list
   - Quick start: Prerequisites (Docker, Python 3.12), then just `make setup && make run`
   - API documentation: link to /docs (Swagger UI)
   - API endpoints table (copy from CLAUDE.md)
   - Architecture overview (brief — reference ARCHITECTURE.md for details)
   - Running tests: `make test`
   - Seed data description

4. CREATE ARCHITECTURE.md:
   - Architecture choice: 3-Layer + Domain Kernel
   - Why not full hexagonal (proportional to scope, same benefits with less ceremony)
   - Layer responsibilities (one paragraph each)
   - Data flow diagram (text-based)
   - Domain layer design: validation functions as the "hex touch"
   - Schema design decisions (uuid7, no deletes, status lifecycles, NULL returned_at pattern)
   - Trade-offs acknowledged

5. CREATE docs/ folder with:
   - docs/api-examples.md: curl examples for every endpoint (create book, borrow, return, list overdue)
```

---

## Prompt 7 — Tests

```
Create all test files. Read CLAUDE.md "Testing (Sync)" for conventions.

1. CREATE tests/conftest.py:
   - Create a test database: use SQLite in-memory (sqlite:////:memory:) for simplicity
   - Create engine, create all tables from Base.metadata
   - Session fixture: yields a session, rolls back after each test
   - Client fixture: FastAPI TestClient with get_db dependency overridden to use test session
   - Sample data fixtures: sample_book, sample_member, sample_borrow

2. CREATE tests/test_domain.py — Test domain validation functions (pure Python, no DB):
   - test_valid_book_transitions: available→borrowed OK, available→retired OK
   - test_invalid_book_transitions: retired→available raises, borrowed→retired raises
   - test_valid_member_transitions: active→inactive OK, suspended→active OK
   - test_invalid_member_transitions: inactive→suspended raises
   - test_calculate_due_date: borrowed_at + 14 days
   - test_is_overdue: past due + not returned = True, past due + returned = False
   - test_validate_borrow_is_active: returned_at=None OK, returned_at set raises

3. CREATE tests/test_services.py — Test business logic with real DB:
   - test_create_book: happy path
   - test_create_member_duplicate_email: should raise error
   - test_borrow_book_success: active member borrows available book
   - test_borrow_unavailable_book: should raise BookNotAvailableError
   - test_borrow_by_inactive_member: should raise MemberNotActiveError
   - test_borrow_already_borrowed_book: should raise BookAlreadyBorrowedError
   - test_return_book_success: sets returned_at, flips book to available
   - test_return_already_returned: should raise BookAlreadyReturnedError
   - test_book_status_transition_retire: available→retired OK
   - test_book_status_transition_retire_borrowed: should raise BookRetirementError

4. CREATE tests/test_api.py — Test HTTP endpoints via TestClient:
   - test_health_check: GET /api/v1/health → 200
   - test_create_book: POST /api/v1/books → 201 + Location header
   - test_list_books: GET /api/v1/books → 200 with pagination
   - test_get_book_not_found: GET /api/v1/books/{bad_id} → 404
   - test_create_member: POST /api/v1/members → 201
   - test_borrow_book: POST /api/v1/borrows → 201
   - test_borrow_unavailable: POST /api/v1/borrows with borrowed book → 409
   - test_return_book: PATCH /api/v1/borrows/{id}/return → 200
   - test_list_overdue: GET /api/v1/borrows?overdue=true → returns only overdue borrows
   - test_filter_by_member: GET /api/v1/borrows?member_id=xxx → filtered results

Run: pytest -v
All tests should pass.
```

---

## Backend Execution Summary

| Step | Command in Claude Code | Expected Time |
|------|----------------------|---------------|
| 1 | Paste Prompt 1 | ~3 min |
| 2 | Paste Prompt 2 (or `/create-model book`, `/create-model member`, `/create-model borrow`) | ~2 min |
| 3 | Paste Prompt 3 (or use slash commands for each) | ~3 min |
| 4 | Paste Prompt 4 (or `/create-service book`, `/create-service member`, `/create-service borrow`) | ~3 min |
| 5 | Paste Prompt 5 (or `/create-route books`, `/create-route members`, `/create-route borrows`) | ~2 min |
| 6 | Paste Prompt 6 | ~3 min |
| 7 | Paste Prompt 7 (or `/create-test domain`, `/create-test services`, `/create-test api`) | ~3 min |

**Total: ~20 minutes for a complete, working, tested backend.**

## Backend Post-Build Checklist
- [ ] `docker-compose up` starts PostgreSQL + app without errors
- [ ] `make migrate` creates all tables
- [ ] `make seed` loads demo data
- [ ] Visit http://localhost:8000/docs — all endpoints visible
- [ ] POST /api/v1/books works → 201
- [ ] POST /api/v1/borrows works → 201 (active member + available book)
- [ ] POST /api/v1/borrows fails → 409 (already borrowed book)
- [ ] PATCH /api/v1/borrows/{id}/return works → 200
- [ ] GET /api/v1/borrows?overdue=true returns overdue borrows
- [ ] `make test` — all tests pass

---
---

# Part 2 — Frontend Prompts (Next.js)

> **Prerequisites:** Backend must be running (`make demo` or `make dev`) before starting frontend.
> **Model:** Use Sonnet for all frontend prompts.
> **Context management:** Run `/clear` between F3→F4 and F5→F6.

---

## Prompt F1 — Scaffold + Layout + API Client + Types

```
Read CLAUDE.md "Frontend — Next.js App" section thoroughly.

Create a Next.js 14 frontend in the frontend/ directory:

1. INITIALIZE Next.js project:
   - Run: npx create-next-app@latest frontend --typescript --tailwind --app --src-dir --no-eslint --import-alias "@/*"
   - cd frontend
   - Install shadcn: npx shadcn@latest init (default style, stone base color, CSS variables yes)
   - Add components: npx shadcn@latest add button table badge input dialog select card separator toast tabs
   - lucide-react is already included with shadcn

2. CREATE frontend/.env.example:
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

3. CREATE frontend/.env.local:
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

4. CREATE frontend/src/types/index.ts:
   - TypeScript interfaces matching backend Pydantic schemas exactly:
   - Book: id, title, author, isbn, publisher, publication_year, genre, status ("available"|"borrowed"|"retired"), created_at, updated_at
   - Member: id, name, email, phone, address, status ("active"|"inactive"|"suspended"), created_at, updated_at
   - Borrow: id, book_id, member_id, borrowed_at, due_date, returned_at (nullable), notes, created_at, book: Book, member: Member
   - PaginatedResponse<T>: items: T[], total, page, size, pages

5. CREATE frontend/src/lib/api.ts:
   - Base URL from NEXT_PUBLIC_API_URL env var
   - Generic fetchAPI<T>(path, options?) helper with error handling
   - Export typed functions:
     - getBooks(params?) → PaginatedResponse<Book>
     - createBook(data) → Book
     - updateBookStatus(id, status) → Book
     - getMembers(params?) → PaginatedResponse<Member>
     - createMember(data) → Member
     - updateMemberStatus(id, status) → Member
     - getBorrows(params?) → PaginatedResponse<Borrow>
     - createBorrow(data) → Borrow
     - returnBorrow(id) → Borrow
   - Query params built from object: Object.entries → filter nulls → URLSearchParams

6. CREATE frontend/src/lib/utils.ts (alongside any existing cn() util from shadcn):
   - formatDate(isoString): returns readable date like "Jan 15, 2026"
   - formatDateTime(isoString): returns "Jan 15, 2026 3:30 PM"
   - getStatusColor(entity: "book"|"member"|"borrow", status): returns tailwind badge variant
     - book: available→green, borrowed→amber, retired→gray
     - member: active→green, inactive→gray, suspended→red
   - isOverdue(due_date, returned_at): boolean check

7. CREATE frontend/src/components/layout/Sidebar.tsx:
   - Fixed left sidebar, w-64, full height, stone-50 background
   - Top: Library icon + "Neighborhood Library" text
   - Nav links with lucide icons:
     - LayoutDashboard → / (Dashboard)
     - BookOpen → /books (Books)
     - Users → /members (Members)
     - ArrowLeftRight → /borrows (Borrows)
   - Active link highlighted with stone-200 background
   - Use next/link and usePathname() for active detection

8. UPDATE frontend/src/app/layout.tsx:
   - Import and render Sidebar on left side
   - Main content area with padding on the right
   - Add Toaster from shadcn for notifications
   - Warm neutral background (bg-stone-100)

9. CREATE frontend/src/app/page.tsx:
   - Simple placeholder: "Dashboard — coming next" with 3 empty shadcn Card placeholders
   - "use client" directive

Verify: cd frontend && npm run dev — loads at localhost:3000, sidebar renders with navigation links, clicking links changes URL.
```

---

## Prompt F2 — Dashboard Page

```
Read CLAUDE.md "Frontend — Pages Overview — Dashboard".

Update frontend/src/app/page.tsx to build the full dashboard:

1. STAT CARDS (3 cards in a responsive grid):
   - Card 1: BookOpen icon + total book count + "Total Books" label
   - Card 2: Users icon + active member count + "Active Members" label
   - Card 3: ArrowLeftRight icon + active borrow count + "Active Borrows" label
   - Fetch counts:
     - GET /books?size=1 → use response.total
     - GET /members?status=active&size=1 → use response.total
     - GET /borrows?active=true&size=1 → use response.total
   - Cards use shadcn Card, large number (text-3xl font-bold), subtle icon

2. OVERDUE ALERT:
   - Fetch GET /borrows?overdue=true&size=1 → get total
   - If total > 0: amber/red banner with AlertTriangle icon, "{count} overdue borrows" + link to /borrows
   - If total == 0: green banner "All books returned on time"

3. RECENT ACTIVITY:
   - Fetch GET /borrows?size=5 → last 5 borrows
   - Card with title "Recent Borrows"
   - Each item: member name + "borrowed" + book title + "— due" + formatted date
   - Status badge next to each (active/overdue/returned using isOverdue util)

4. Loading state:
   - useState for loading boolean
   - Show 3 skeleton cards (animate-pulse) while fetching
   - useEffect fetches all data on mount

Verify: Dashboard shows real counts from seeded data. Overdue alert shows "1 overdue borrow" (from seed). Recent borrows list shows seeded records.
```

---

## Prompt F3 — Books Page

```
Read CLAUDE.md "Frontend — Pages Overview — Books".

1. CREATE frontend/src/components/books/BookFormModal.tsx:
   - shadcn Dialog component
   - Form fields: title (required), author (required), isbn, publisher, publication_year (number), genre
   - Props: open, onOpenChange, onSuccess (callback to refetch)
   - Submit: call createBook() from lib/api.ts
   - On success: toast("Book added"), call onSuccess(), close dialog
   - On error: toast with error message
   - Basic validation: title and author must not be empty

2. CREATE frontend/src/components/books/BookTable.tsx:
   - Props: books: Book[], onRefresh (callback)
   - shadcn Table with columns: Title, Author, ISBN, Genre, Status, Actions
   - ISBN: show "—" if null
   - Genre: show "—" if null
   - Status: shadcn Badge with color from getStatusColor("book", status)
   - Actions column:
     - If status == "available": "Retire" button (destructive variant, small)
     - If status == "borrowed": show "Borrowed" text (no action)
     - If status == "retired": show "Retired" text (no action)
   - Retire click: call updateBookStatus(id, "retired"), toast, call onRefresh()
   - Empty state: "No books found" message when list is empty

3. UPDATE frontend/src/app/books/page.tsx:
   - "use client" directive
   - Page header row: "Books" title (text-2xl font-bold) + "Add Book" button (opens BookFormModal)
   - Search input: debounced (300ms) text input, updates search param
   - Status filter: shadcn Select with options: All, Available, Borrowed, Retired
   - BookTable below filters
   - Pagination controls at bottom: "Page X of Y" with Previous/Next buttons
   - State: books[], total, page, size, search, statusFilter, loading
   - useEffect: fetch books whenever page, search, or statusFilter changes
   - Loading: show skeleton rows while fetching

Verify: Books page lists 5 seeded books. Search "fowler" shows Refactoring. Filter "available" shows 3 books. "Add Book" creates new book. "Retire" changes available book to retired.
```

---

## Prompt F4 — Members Page

```
Read CLAUDE.md "Frontend — Pages Overview — Members".
Follow the EXACT same component patterns as the Books page.

1. CREATE frontend/src/components/members/MemberFormModal.tsx:
   - Same pattern as BookFormModal
   - Fields: name (required), email (required), phone (optional), address (optional)
   - Submit: call createMember()
   - Validate email format (basic check: includes "@")

2. CREATE frontend/src/components/members/MemberTable.tsx:
   - Same pattern as BookTable
   - Columns: Name, Email, Phone, Status, Actions
   - Phone: show "—" if null
   - Status: Badge with getStatusColor("member", status)
   - Actions based on current status:
     - active: "Suspend" button (destructive) + "Deactivate" button (secondary)
     - inactive: "Activate" button (default/green)
     - suspended: "Activate" button (default/green)
   - Each action: call updateMemberStatus(id, newStatus), toast, onRefresh()

3. UPDATE frontend/src/app/members/page.tsx:
   - Same structure as books/page.tsx
   - Header: "Members" + "Add Member" button
   - Search + status filter (All/Active/Inactive/Suspended)
   - MemberTable + pagination

Verify: Members page lists 3 seeded members. "Suspend" on Alice works. "Activate" on Bob works. "Add Member" creates new member.
```

---

## Prompt F5 — Borrows Page

```
Read CLAUDE.md "Frontend — Pages Overview — Borrows".

1. CREATE frontend/src/components/borrows/BorrowFormModal.tsx:
   - shadcn Dialog
   - Two select dropdowns:
     - "Select Book": fetches GET /books?status=available&size=100 on dialog open
       - Shows: "Title — Author" for each available book
     - "Select Member": fetches GET /members?status=active&size=100 on dialog open
       - Shows: "Name (email)" for each active member
   - Optional notes textarea
   - Submit: call createBorrow({ book_id, member_id, notes })
   - Both selects required — show validation error if empty
   - On success: toast("Book borrowed successfully"), onSuccess(), close

2. CREATE frontend/src/components/borrows/BorrowTable.tsx:
   - Props: borrows: Borrow[], onRefresh
   - Columns: Book Title, Member Name, Borrowed, Due Date, Status, Actions
   - Borrowed: formatDate(borrowed_at)
   - Due Date: formatDate(due_date)
   - Status logic:
     - returned_at != null → Badge "Returned" (green)
     - isOverdue(due_date, returned_at) → Badge "Overdue" (red)
     - else → Badge "Active" (blue)
   - OVERDUE rows: add subtle red/rose background tint (bg-red-50)
   - Actions:
     - If active or overdue: "Return" button
     - If returned: show formatted returned_at date
   - Return click: call returnBorrow(id), toast("Book returned"), onRefresh()

3. UPDATE frontend/src/app/borrows/page.tsx:
   - Header: "Borrows" + "Borrow Book" button
   - Filter using shadcn Tabs (not dropdown):
     - "All" tab: no filter params
     - "Active" tab: active=true
     - "Overdue" tab: overdue=true
     - "Returned" tab: active=false
   - BorrowTable below tabs
   - Pagination controls
   - State: borrows[], total, page, activeTab, loading
   - useEffect: refetch when page or activeTab changes

Verify: Borrows page shows 3 seeded borrows. "Design Patterns" borrow shows as "Overdue" with red tint. "Clean Code" borrow shows as "Returned". Return button works on active borrows. "Borrow Book" modal shows only available books and active members.
```

---

## Prompt F6 — Docker + Devbox + Final Wiring

```
Wire the frontend into Docker Compose and add devbox support for local dev.

1. CREATE frontend/Dockerfile:
   FROM node:20-alpine AS base

   FROM base AS deps
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci

   FROM base AS builder
   WORKDIR /app
   COPY --from=deps /app/node_modules ./node_modules
   COPY . .
   ENV NEXT_TELEMETRY_DISABLED=1
   RUN npm run build

   FROM base AS runner
   WORKDIR /app
   ENV NODE_ENV=production
   ENV NEXT_TELEMETRY_DISABLED=1
   COPY --from=builder /app/public ./public
   COPY --from=builder /app/.next/standalone ./
   COPY --from=builder /app/.next/static ./.next/static
   EXPOSE 3000
   CMD ["node", "server.js"]

2. UPDATE frontend/next.config.ts:
   - Add output: "standalone" (required for Docker multi-stage build)
   - Add rewrites for local dev (proxy /api to backend):
     async rewrites() {
       return [{ source: "/api/:path*", destination: "http://localhost:8000/api/:path*" }];
     }

3. UPDATE docker-compose.yml (project root — do NOT overwrite, ADD to existing):
   - Add frontend service:
     frontend:
       build: ./frontend
       container_name: library-frontend
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
       depends_on:
         backend:
           condition: service_healthy
       networks:
         - library-network

4. CREATE frontend/devbox.json:
   {
     "packages": ["nodejs@20", "gnumake@latest"],
     "shell": {
       "init_hook": [
         "echo 'Frontend — Neighborhood Library'",
         "if [ ! -d node_modules ]; then echo 'Installing deps...'; npm install; fi",
         "echo ''",
         "echo 'Ready! Run: npm run dev'"
       ]
     }
   }

5. UPDATE root Makefile:
   - Update demo target: add wait for frontend container to be healthy after backend
   - Update demo success banner to include: "Frontend  http://localhost:3000"
   - Add new targets:
     frontend-dev:
       cd frontend && npm run dev
     frontend-build:
       cd frontend && npm run build

6. UPDATE root README.md:
   - Add "Frontend" section under Tech Stack: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
   - Update Quick Start: mention frontend at http://localhost:3000
   - Add "Local Frontend Development" section:
     cd frontend && devbox shell && npm run dev
     OR: cd frontend && npm install && npm run dev
   - Update make demo output description to include frontend

7. ADD frontend/.gitignore:
   node_modules/
   .next/
   out/
   .env.local

Verify:
- make demo starts db + backend + frontend (all 3 containers)
- http://localhost:3000 loads dashboard with real data
- http://localhost:8000/docs still works
- cd frontend && npm run dev works for local frontend dev
- All pages functional: dashboard, books, members, borrows
```

---

## Frontend Execution Summary

| Step | Prompt | Model | Expected Time |
|------|--------|-------|---------------|
| F1 | Scaffold + Layout + API + Types | Sonnet | ~5 min |
| F2 | Dashboard | Sonnet | ~3 min |
| F3 | Books page | Sonnet | ~4 min |
| — | `/clear` | — | — |
| F4 | Members page | Sonnet | ~3 min |
| F5 | Borrows page | Sonnet | ~4 min |
| — | `/clear` | — | — |
| F6 | Docker + Devbox wiring | Sonnet | ~3 min |

**Total: ~22 minutes for a polished, functional frontend.**

## Frontend Post-Build Checklist
- [ ] `make demo` starts all 3 services (db, backend, frontend)
- [ ] http://localhost:3000 — Dashboard loads with stats and overdue alert
- [ ] /books — List, search, filter, add book, retire book all work
- [ ] /members — List, search, add member, suspend/activate work
- [ ] /borrows — List, filter tabs (All/Active/Overdue/Returned) work
- [ ] /borrows — "Borrow Book" modal shows only available books + active members
- [ ] /borrows — "Return" button works, book becomes available again
- [ ] /borrows — Overdue rows highlighted with red tint
- [ ] Toast notifications appear on success and error
- [ ] Frontend works via Docker (`make demo`) AND locally (`cd frontend && npm run dev`)

---

## Full Project — Combined Execution

| Phase | Prompts | Time |
|-------|---------|------|
| Backend | 1 → 7 | ~20 min |
| Frontend | F1 → F6 | ~22 min |
| **Total** | **13 prompts** | **~42 min** |

## Final Deliverable Checklist
- [ ] `make demo` — one command starts everything
- [ ] Backend API: http://localhost:8000/docs
- [ ] Frontend UI: http://localhost:3000
- [ ] All CRUD operations work end-to-end
- [ ] Borrow rules enforced (can't borrow borrowed book, can't borrow as suspended member)
- [ ] Overdue detection works
- [ ] Tests pass: `make test`
- [ ] README.md explains setup clearly
- [ ] ARCHITECTURE.md explains design decisions
- [ ] docs/api-examples.md has curl examples
