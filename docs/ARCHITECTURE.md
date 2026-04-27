# Architecture

## Design Choice: 3-Layer + Domain Kernel

This project uses a **3-Layer + Domain Kernel** architecture rather than full Hexagonal (Ports & Adapters). The trade-off is intentional: Hexagonal architecture's port/adapter ceremony is disproportionate for a bounded, single-database CRUD service. The same benefits — testability, clear separation of concerns, domain logic isolated from infrastructure — are achieved here with less indirection.

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Routes  (app/api/routes/)                          │
│  HTTP concerns only: parse request, call service,   │
│  return correct status code and response schema.    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  Services  (app/services/)                          │
│  ALL business logic: status transitions, borrow     │
│  rules, domain validation, orchestration.           │
└───────────┬────────────────────────┬────────────────┘
            │                        │
            ▼                        ▼
┌─────────────────────┐   ┌─────────────────────────────┐
│  Domain Kernel      │   │  Repositories               │
│  (app/domain/)      │   │  (app/database/repositories)│
│  Pure Python.       │   │  Database queries only.     │
│  Enums, exceptions, │   │  No business logic.         │
│  validation rules.  │   │  Receive Session via DI.    │
└─────────────────────┘   └──────────────┬──────────────┘
                                         │
                                         ▼
                               ┌──────────────────┐
                               │  PostgreSQL 15   │
                               │  (SQLAlchemy 2.0)│
                               └──────────────────┘
```

## Layer Responsibilities

**Routes** are thin HTTP adapters. They parse the incoming request body into a Pydantic schema, call one service method, and return the result as a response schema with the correct HTTP status code. No business logic lives here — not even "is the user authorized to do this."

**Services** own all application logic. Every borrowing rule, every status transition validation, every invariant check lives in a service method. Services call domain validation functions (the "anti-corruption touch") before mutating state, and delegate all data access to repositories. Services do not know about HTTP.

**Repositories** are query objects. Each repository method executes one database operation and returns a model instance or list. No if-statements, no business rules. The session is injected via FastAPI's `Depends()` chain so tests can swap it out cleanly.

**Domain Kernel** is pure Python with zero framework imports. It defines the enums that give status values meaning, the exceptions that represent business rule violations, and small validation functions (`validate_book_status_transition`, `validate_borrow_is_active`) that encode invariants once and are called by services. This is the "hexagonal touch" — the domain has no idea it's running inside FastAPI or talking to Postgres.

**Schemas** (Pydantic v2) are the anti-corruption layer at the API boundary. They validate and coerce incoming JSON, and serialize outgoing ORM objects. They are not domain objects — they live in `app/api/schemas/` and are not imported by repositories or domain code.

## Domain Layer Design

Status transitions are encoded as explicit dictionaries:

```python
BOOK_STATUS_TRANSITIONS = {
    BookStatus.AVAILABLE: [BookStatus.BORROWED, BookStatus.RETIRED],
    BookStatus.BORROWED:  [BookStatus.AVAILABLE],
    BookStatus.RETIRED:   [],  # terminal state
}
```

A single `validate_book_status_transition(current, new)` function is the single source of truth for what moves are legal. Services call it; tests call it directly. No scattered if-chains across route handlers.

## Schema Design Decisions

**UUID v7 primary keys** — time-sortable, globally unique, safe for distributed systems. Avoids the sequential-ID enumeration attack and gives natural ordering without an extra `ORDER BY created_at`.

**No DELETE endpoints** — lifecycle is managed by status fields. Books and members are never hard-deleted. This preserves audit trail, avoids FK cascade complexity, and lets overdue records remain queryable after a member is suspended.

**`returned_at IS NULL` as the "active borrow" sentinel** — cleaner than a boolean `is_active` flag that would need to stay in sync. A single partial index on `(book_id, returned_at)` answers "is this book currently borrowed?" efficiently.

**Timestamps with timezone** — all `datetime` columns use `DateTime(timezone=True)`. Timestamps are stored and compared in UTC throughout the service layer.

**No `updated_at` on borrows** — borrow records are append-only. They are created (borrowed) and then finalized (returned). There is no edit operation, so an `updated_at` column would always equal `created_at` and be misleading.

**Unique nullable ISBN** — ISBN is optional (donated books may not have one) but unique when present. PostgreSQL treats multiple `NULL` values as distinct in a unique index, so this works without special handling.

## Trade-offs Acknowledged

- **No async** — chosen deliberately per spec. Sync SQLAlchemy with a connection pool handles typical library-scale traffic fine. Switching to async later requires replacing `create_engine` → `create_async_engine`, `Session` → `AsyncSession`, and adding `await` at every query call site.
- **Services hold repositories directly** — no interface/port abstraction. This means swapping the database requires changing the service, not just the DI wiring. Acceptable trade-off given the scope.
- **No caching layer** — book lists and member lookups could be cached. Not needed at this scale.
- **No event bus** — returning a book and updating its status is a single transaction. In a distributed system this would be an event (`BookReturned`) consumed by a status projection. Not warranted here.

---

## Known Design Decisions

### Duplicate Books Are Allowed (Intentional)
Multiple rows with the same `(title, author)` are permitted. A neighborhood library can own several physical copies of the same book; each copy is a distinct borrowable item that needs its own lifecycle. The `isbn` unique constraint covers the most common accidental-duplicate case (ISBN is unique when present). No service-layer deduplication check was added — this is a deliberate choice, not an oversight.

### Duplicate Members Are Prevented by Email (Intentional)
`email` carries a `UNIQUE` constraint at the database level. No additional service-layer check is needed; the database rejects duplicates and FastAPI surfaces the integrity error as a 422.

### Suspended/Inactive Members Keep Their Active Borrows (Intentional)
Deactivating or suspending a member does **not** auto-return their outstanding books. The books stay in `borrowed` status. This is intentional: forcing a return would corrupt the audit trail. Staff must handle outstanding books manually before suspending a member in practice.

### Book Status Is Owned by Two Code Paths (Intentional)
`book.status` is set to `borrowed` when a borrow is created and back to `available` when it is returned. The `PATCH /api/v1/books/{id}/status` endpoint also allows direct status changes (e.g., retiring a book). Both paths go through `validate_book_status_transition` in the domain layer, so the same invariants apply. There is no race condition at library scale with a single Postgres instance.

### No Soft-Delete, No Audit Log Table (Intentional)
Status fields serve as soft-delete. `created_at` / `updated_at` timestamps provide a basic audit trail. A dedicated audit-log table (who changed what and when) would add value in production but is out of scope for this assignment.

---

## Known Issues

### No Uniqueness Guard for ISBN-less Books
Two staff members can independently add the same donated book (no ISBN) and the system will accept both rows. This creates phantom inventory. Mitigation options: (a) require ISBN for all books, (b) add a service-layer check on `(title, author)`, (c) add a partial unique index `UNIQUE(title, author) WHERE isbn IS NULL`. None were implemented because multi-copy ownership is a valid use case and the fix would block it.

### No Concurrency Guard on Borrow Creation
If two requests attempt to borrow the same book simultaneously, both may read `status = available` before either commits. The second commit will put the book into an inconsistent state (two active borrows, status = borrowed). Fix: add a `SELECT ... FOR UPDATE` lock in `BorrowRepository.create` or a database-level partial unique index `UNIQUE(book_id) WHERE returned_at IS NULL`. Not implemented — acceptable at library scale with a single app instance.

### No Member Borrow Limit
A member can hold an unlimited number of books simultaneously. A real library would cap this (e.g., 5 books per member). The domain layer has no `MAX_ACTIVE_BORROWS` constant and the borrow service has no check. Easy to add: query active borrow count in `BorrowService.borrow_book` and raise a domain exception if exceeded.

### Overdue Detection Is Read-Only
`is_overdue()` in the domain layer is a pure function called at read time. There is no background job that marks borrows or members as overdue. Overdue borrows surface only when the caller passes `?overdue=true` to `GET /api/v1/borrows`. A cron job or scheduled task that notifies members or flags accounts was out of scope.

### No Authentication or Authorization
All endpoints are publicly accessible. Any caller can register members, borrow books, or retire inventory. Adding OAuth2/JWT would require a `current_user` dependency and per-endpoint permission checks — intentionally omitted for the take-home scope.
