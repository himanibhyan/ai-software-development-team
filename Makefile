.PHONY: help install dev build up down migrate lint test clean

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	cd backend && pip install -r requirements/base.txt

dev: ## Install development dependencies
	cd backend && pip install -r requirements/dev.txt

build: ## Build Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

dev-up: ## Start infrastructure services only (postgres, redis, chroma)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis chromadb

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-new: ## Create a new migration
	cd backend && alembic revision --autogenerate -m "$(name)"

lint: ## Run linters
	cd backend && ruff check app/ tests/
	cd backend && mypy app/ --ignore-missing-imports

lint-fix: ## Auto-fix lint issues
	cd backend && ruff check --fix app/ tests/

test: ## Run tests
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=term-missing

test-unit: ## Run unit tests only
	cd backend && python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	cd backend && python -m pytest tests/integration/ -v

clean: ## Clean cache and build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/
