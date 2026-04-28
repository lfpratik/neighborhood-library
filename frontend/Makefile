.DEFAULT_GOAL := help

.PHONY: help install dev build start lint typecheck clean docker-build docker-run docker-stop docker-logs

# -------- Help --------
help:
	@echo ""
	@echo "Neighborhood Library — Frontend"
	@echo "================================"
	@echo ""
	@echo "  make install     Install npm dependencies"
	@echo "  make dev         Start dev server on :3000 (hot reload)"
	@echo "  make build       Production build"
	@echo "  make start       Start production server (requires build first)"
	@echo "  make typecheck   Run TypeScript type checker"
	@echo "  make typecheck   Run TypeScript type checker"
	@echo "  make clean       Remove .next/ build output"
	@echo "  make clean-all   Full reset (node_modules, build, env files)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  Build the Docker image"
	@echo "  make docker-run    Run the container on :3000"
	@echo "  make docker-stop   Stop and remove the container"
	@echo "  make docker-logs   Tail container logs"
	@echo ""

# -------- Setup --------
install:
	@test -f .env.local || cp .env.example .env.local
	npm install

# -------- Dev --------
dev:
	npm run dev

# -------- Build --------
build:
	npm run build

start: build
	npm run start

# -------- Quality --------
typecheck:
	npx tsc --noEmit

# -------- Docker --------
docker-build:
	@test -f .env.docker || cp .env.example .env.docker
	set -a && . ./.env.docker && set +a && \
	docker build \
		--build-arg NEXT_PUBLIC_API_URL=$${NEXT_PUBLIC_API_URL} \
		-t library-frontend .

docker-run: docker-build
	docker run -d \
		--name library-frontend \
		-p 3000:3000 \
		library-frontend
	@echo "Frontend running at http://localhost:3000"

docker-stop:
	docker stop library-frontend 2>/dev/null || true
	docker rm library-frontend 2>/dev/null || true

docker-logs:
	docker logs -f library-frontend

# -------- Clean --------
clean:
	rm -rf .next

clean-all: clean
	rm -rf node_modules
	rm -rf .devbox
	rm -rf .env.local
	rm -rf .env.docker
