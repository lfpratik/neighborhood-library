# -------- Variables --------
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PYTEST := $(VENV)/bin/pytest
ALEMBIC := $(VENV)/bin/alembic
RUFF := ruff

APP := app.main:app
PORT := 8000

.DEFAULT_GOAL := help

# -------- Phony Targets --------
.PHONY: help venv install install-force dev migration migrate seed seed-force test lint lint-fix format typecheck clean clean-all demo build run up down logs docker-seed docker-seed-force

# -------- Help --------
help:
	@echo ""
	@echo "Neighborhood Library API"
	@echo "========================"
	@echo ""
	@echo "  make demo       ★ Full Docker demo: build + migrate + seed (start here)"
	@echo "  make run          Start all Docker services (if already built)"
	@echo "  make down         Stop Docker services"
	@echo "  make logs         Tail backend logs"
	@echo ""
	@echo "Local development:"
	@echo "  make install      Setup virtualenv & install dependencies"
	@echo "  make dev          Start FastAPI server locally (requires local Postgres)"
	@echo "  make migrate      Apply DB migrations"
	@echo "  make seed         Seed database"
	@echo "  make test         Run test suite"
	@echo "  make lint         Run ruff lint"
	@echo "  make format       Format code"
	@echo "  make typecheck    Run mypy type checks"
	@echo "  make clean        Remove Python cache"
	@echo "  make clean-all    Full reset (venv + docker volumes)"
	@echo "  make build        Build Docker images"
	@echo "  make up           Start services with Docker Compose"
	@echo ""

# -------- Local Setup --------
venv:
	@ [ -d $(VENV) ] || python3 -m venv $(VENV)

install: venv
	@test -f .env.local || cp .env.example .env.local
	@if [ ! -f "$(VENV)/.installed" ]; then \
		$(PIP) install --upgrade pip && \
		$(PIP) install -r requirements.txt && \
		touch $(VENV)/.installed; \
		echo "Dependencies installed"; \
	else \
		echo "Dependencies already installed (skip)"; \
	fi

install-force: venv
	rm -f $(VENV)/.installed
	$(PIP) install --upgrade pip && \
	$(PIP) install -r requirements.txt && \
	touch $(VENV)/.installed

# -------- Local Dev --------
dev: install
	$(UVICORN) $(APP) --reload --host 0.0.0.0 --port $(PORT)

# -------- Migrations --------
migrate:
	$(ALEMBIC) upgrade head

migration:
	$(ALEMBIC) revision --autogenerate -m "$(m)"

# -------- Seed --------
seed:
	@if [ ! -f "$(VENV)/.seeded" ]; then \
		$(PYTHON) scripts/seed.py && \
		touch $(VENV)/.seeded; \
		echo "Database seeded"; \
	else \
		echo "Already seeded (skip). Run 'make seed-force' to re-seed"; \
	fi

seed-force:
	rm -f $(VENV)/.seeded
	$(PYTHON) scripts/seed.py
	touch $(VENV)/.seeded

# -------- Tests --------
test:
	$(PYTEST) -v

# -------- Dev Tools --------
lint:
	$(RUFF) check app tests scripts

lint-fix:
	$(RUFF) check --fix app tests scripts

format:
	$(RUFF) format app tests scripts

typecheck:
	$(PYTHON) -m mypy app tests scripts

# -------- Clean --------
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean
	rm -rf $(VENV)
	rm -rf .devbox
	rm -rf .direnv
	docker-compose down -v --remove-orphans

# -------- Demo with Docker --------

demo:
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║       Neighborhood Library API — Demo        ║"
	@echo "╚══════════════════════════════════════════════╝"
	@echo ""
	@echo "Stack: FastAPI · PostgreSQL · SQLAlchemy 2.0 · Alembic · Docker"
	@echo ""
	@echo "► Step 1/4  Preparing environment..."
	@test -f .env.docker || sed 's|@localhost:|@db:|g' .env.example > .env.docker
	@echo ""
	@echo "► Step 2/4  Building Docker images..."
	$(MAKE) build
	@echo ""
	@echo "► Step 3/4  Starting services (Postgres → migrations → FastAPI)..."
	$(MAKE) up
	@echo "Waiting for backend to be ready..."
	@until docker-compose exec -T backend curl -sf http://localhost:8000/api/v1/health > /dev/null 2>&1; do \
		printf '.'; sleep 3; \
	done
	@echo " ready!"
	@echo ""
	@echo "► Step 4/4  Seeding demo data..."
	$(MAKE) docker-seed
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║              Demo is ready!                  ║"
	@echo "╠══════════════════════════════════════════════╣"
	@echo "║  API base   http://localhost:8000/api/v1     ║"
	@echo "║  Swagger UI http://localhost:8000/docs       ║"
	@echo "║  ReDoc      http://localhost:8000/redoc      ║"
	@echo "╠══════════════════════════════════════════════╣"
	@echo "║  Seed data:                                  ║"
	@echo "║   5 books  (available / borrowed / retired)  ║"
	@echo "║   3 members (active / inactive / suspended)  ║"
	@echo "║   3 borrows (active / overdue / returned)    ║"
	@echo "╠══════════════════════════════════════════════╣"
	@echo "║  make logs   — tail backend logs             ║"
	@echo "║  make down   — stop everything               ║"
	@echo "╚══════════════════════════════════════════════╝"
	@echo ""

build:
	docker-compose build

run:
	docker-compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "  API:  http://localhost:8000/api/v1"
	@echo "  Docs: http://localhost:8000/docs"

up:
	docker-compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "  API:  http://localhost:8000/api/v1"
	@echo "  Docs: http://localhost:8000/docs"

down:
	docker-compose down

down-all:
	docker-compose down -v --remove-orphans

logs:
	docker-compose logs -f backend

docker-seed:
	@if docker-compose exec -T backend test -f /tmp/.seeded 2>/dev/null; then \
		echo "Already seeded (skip). Run 'make docker-seed-force' to re-seed"; \
	else \
		docker-compose exec -T backend python scripts/seed.py && \
		docker-compose exec -T backend touch /tmp/.seeded; \
		echo "Database seeded"; \
	fi

docker-seed-force:
	docker-compose exec -T backend python scripts/seed.py
	docker-compose exec -T backend touch /tmp/.seeded
