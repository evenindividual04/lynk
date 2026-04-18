.PHONY: dev backend frontend test migrate lint typecheck setup

dev:
	@echo "Starting backend on :8000 and frontend on :5173..."
	@(cd backend && uv run uvicorn src.lynk.main:app --reload --port 8000) & \
	 (cd frontend && pnpm dev) ; wait

backend:
	cd backend && uv run uvicorn src.lynk.main:app --reload --port 8000

frontend:
	cd frontend && pnpm dev

test:
	cd backend && uv run pytest --cov=src/lynk --cov-report=term-missing
	cd frontend && pnpm test

migrate:
	cd backend && uv run alembic upgrade head

migrate-create:
	cd backend && uv run alembic revision --autogenerate -m "$(msg)"

lint:
	cd backend && uv run ruff check .
	cd frontend && pnpm lint

typecheck:
	cd backend && uv run mypy src/
	cd frontend && pnpm typecheck

gen-types:
	cd frontend && pnpm gen:types

setup:
	cp -n .env.example .env || true
	mkdir -p data/imports
	cd backend && uv sync
	cd frontend && pnpm install
	cd backend && uv run alembic upgrade head
	pre-commit install
