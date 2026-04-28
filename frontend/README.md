# Neighborhood Library — Frontend

Next.js 14 frontend for the Neighborhood Library management system.

## Tech Stack

- **Next.js 14** (App Router) · **TypeScript** · **Tailwind CSS** · **shadcn/ui**
- **Lucide React** (icons) · **Sonner** (toasts)

## Quick Start

### Option A — Via Docker (recommended)

Run from the project root — frontend starts automatically with the full stack:

```bash
make demo        # builds + starts db + backend + frontend
```

Frontend available at **http://localhost:3000**

### Option B — Local Dev (Devbox)

```bash
devbox shell     # provisions Node 20, installs deps
make dev         # starts Next.js on :3000 with hot reload
```

### Option C — Local Dev (Manual)

```bash
make install     # npm install + creates .env.local
make dev         # starts Next.js on :3000
```

> **Requires backend running** at `http://localhost:8000`. The dev server proxies `/api/*` → `http://localhost:8000` automatically.

## Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Stats, overdue alert, recent borrows |
| Books | `/books` | List, search, filter, add, retire |
| Members | `/members` | List, search, filter, add, suspend/activate |
| Borrows | `/borrows` | List, filter tabs, borrow, return |

## Make Targets

```bash
make install      # install dependencies
make dev          # start dev server (:3000)
make build        # production build
make start        # build + start production server
make typecheck    # TypeScript type check
make clean        # remove .next/
make clean-all    # remove .next/, node_modules, env files

make docker-build # build Docker image
make docker-run   # run container on :3000
make docker-stop  # stop and remove container
make docker-logs  # tail container logs
```

## Environment

```bash
cp .env.example .env.local
# edit NEXT_PUBLIC_API_URL if your backend runs on a different port
```

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API base URL (baked at build time) |
