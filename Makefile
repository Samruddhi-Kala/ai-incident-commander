.PHONY: dev test docker-up docker-down migrate migration clean help

help:
	@echo "AI Incident Commander — Development Commands"
	@echo "------------------------------------------------"
	@echo "make docker-up    Start PostgreSQL (pgvector) and Redis containers"
	@echo "make docker-down  Stop Docker containers"
	@echo "make dev          Run local FastAPI server with auto-reload"
	@echo "make test         Run backend pytest suite"
	@echo "make migrate      Run Alembic database migrations"
	@echo "make migration    Generate a new Alembic migration"

docker-up:
	docker compose up -d postgres redis

docker-down:
	docker compose down

dev:
	cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest tests/backend

migrate:
	cd backend && alembic upgrade head

migration:
	@read -p "Enter migration description: " desc; \
	cd backend && alembic revision --autogenerate -m "$$desc"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
