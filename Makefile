.PHONY: up down build restart logs shell-backend shell-frontend migrate seed test clean

# ============================================================
# BMIM Development Helpers
# ============================================================

up:
	docker compose up -d

build:
	docker compose up --build -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

# Database migrations
migrate:
	docker compose exec backend alembic upgrade head

# Load seed data
seed:
	docker compose exec backend python -m app.db.seed

# Run all backend tests
test:
	docker compose exec backend pytest tests/ -v

# Run only unit tests
test-unit:
	docker compose exec backend pytest tests/unit/ -v

# Run only integration tests
test-integration:
	docker compose exec backend pytest tests/integration/ -v

# Shell access
shell-backend:
	docker compose exec backend bash

shell-frontend:
	docker compose exec frontend sh

shell-db:
	docker compose exec postgres psql -U bmim_user -d bmim_db

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Full reset (WARNING: deletes all data)
reset: clean build migrate seed

# Local development (without Docker)
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

# Install dependencies locally
install-backend:
	cd backend && pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

# Format + lint
lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff format .

# Generate .env from example
env:
	cp .env.example .env
	@echo ".env created. Please review and update secrets before running."
