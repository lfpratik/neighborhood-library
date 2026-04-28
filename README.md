# Neighborhood Library API

A REST API for managing a neighborhood library — books, members, and lending operations.

## Tech Stack

- **Python 3.11** · **FastAPI** (sync) · **SQLAlchemy 2.0** (sync) · **PostgreSQL 15**
- **Alembic** (migrations) · **Pydantic v2** · **pytest** (tests)
- **Next.js 14** · **TypeScript** · **Tailwind CSS** · **shadcn/ui** (frontend)
- **Docker Compose** (demo) · **Devbox** (local dev)

## Quick Start — Docker Demo

**Prerequisites:** Docker, Docker Compose

```bash
make demo
```

One command: builds images, runs migrations, seeds data, and prints all URLs when ready.

```text
╔══════════════════════════════════════════════╗
║              Demo is ready!                  ║
╠══════════════════════════════════════════════╣
║  Frontend   http://localhost:3000            ║
║  API base   http://localhost:8000/api/v1     ║
║  Swagger UI http://localhost:8000/docs       ║
║  ReDoc      http://localhost:8000/redoc      ║
╚══════════════════════════════════════════════╝
```

```bash
make logs   # tail backend logs
make down   # stop everything
```

## Local Development

### Option A — Devbox (recommended)

**Prerequisites:** [Devbox](https://www.jetify.com/devbox)

```bash
devbox shell      # provisions Python 3.11, activates venv, installs deps
make migrate      # apply migrations against your local Postgres
make seed         # load sample data
make dev          # start server on :8000 with --reload
```

The `devbox shell` init hook installs all dependencies automatically on first run.

### Option B — Manual (Makefile)

**Prerequisites:** Python 3.11, local PostgreSQL

```bash
make install      # create .venv and install dependencies (.env.local created automatically)
# edit .env.local — set DATABASE_URL to your local Postgres
make migrate      # run Alembic migrations
make seed         # load sample data
make dev          # start server on :8000
```

## Local Frontend Development

```bash
cd frontend && devbox shell    # provisions Node 20, installs deps
npm run dev                    # starts Next.js on :3000 with hot reload
```

Or without Devbox:

```bash
cd frontend && npm install && npm run dev
```

The dev server proxies `/api/*` → `http://localhost:8000` so the backend can run separately.

## API Documentation

- Swagger UI: **<http://localhost:8000/docs>**
- ReDoc: **<http://localhost:8000/redoc>**
- OpenAPI spec: **<http://localhost:8000/openapi.json>**

Import the OpenAPI spec directly into Postman or Insomnia — see [docs/api-examples.md](docs/api-examples.md#postman--insomnia) for step-by-step instructions.

## Endpoints

### Books

| Method | Endpoint                   | Status Codes    | Description        |
|--------|----------------------------|-----------------|--------------------|
| POST   | /api/v1/books              | 201, 422        | Add new book       |
| GET    | /api/v1/books              | 200             | List/search books  |
| GET    | /api/v1/books/{id}         | 200, 404        | Get book detail    |
| PUT    | /api/v1/books/{id}         | 200, 404, 422   | Update book info   |
| PATCH  | /api/v1/books/{id}/status  | 200, 404, 409   | Change book status |

### Members

| Method | Endpoint                     | Status Codes    | Description          |
|--------|------------------------------|-----------------|----------------------|
| POST   | /api/v1/members              | 201, 422        | Register member      |
| GET    | /api/v1/members              | 200             | List/search members  |
| GET    | /api/v1/members/{id}         | 200, 404        | Get member detail    |
| PUT    | /api/v1/members/{id}         | 200, 404, 422   | Update member info   |
| PATCH  | /api/v1/members/{id}/status  | 200, 404, 409   | Change member status |

### Borrows

| Method | Endpoint                      | Status Codes        | Description      |
|--------|-------------------------------|---------------------|------------------|
| POST   | /api/v1/borrows               | 201, 404, 409, 422  | Borrow a book    |
| GET    | /api/v1/borrows               | 200                 | List borrows     |
| GET    | /api/v1/borrows/{id}          | 200, 404            | Get borrow       |
| PATCH  | /api/v1/borrows/{id}/return   | 200, 404, 409       | Return a book    |

### System

| Method | Endpoint        | Description            |
|--------|-----------------|------------------------|
| GET    | /api/v1/health  | Health check + DB ping |

## Architecture

3-Layer + Domain Kernel: Routes → Services → Repositories → Database, with a pure-Python Domain layer for enums, exceptions, and validation rules.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full design rationale.

## Running Tests

```bash
make test
```

Tests use `TestClient` (sync) against an in-memory SQLite database — no external DB required.

## Seed Data

`make demo` and `make seed` both load:

- **5 books**: Clean Code, Design Patterns, The Pragmatic Programmer (available); Refactoring, Design Patterns (borrowed); The Mythical Man-Month (retired)
- **3 members**: Alice Johnson (active), Bob Smith (inactive), Charlie Brown (suspended)
- **3 borrows**: 1 active (due in 9 days), 1 active overdue (6 days past due), 1 completed (returned)

See [docs/api-examples.md](docs/api-examples.md) for curl examples.
