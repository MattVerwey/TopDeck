.PHONY: help install install-dev test lint format type-check clean run docker-up docker-down

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

test: ## Run tests with coverage
	pytest -v --cov=topdeck --cov-report=term-missing --cov-report=html

test-fast: ## Run tests without coverage
	pytest -v

lint: ## Run linters
	ruff check src tests
	black --check src tests

format: ## Format code with black and ruff
	ruff check --fix src tests
	black src tests

type-check: ## Run type checking with mypy
	mypy src

clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov coverage.xml .coverage
	rm -rf dist build *.egg-info

run: ## Run the API server
	python -m topdeck

docker-up: ## Start Docker services (Neo4j, Redis, RabbitMQ)
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker service logs
	docker-compose logs -f

check: lint type-check test ## Run all checks (lint, type-check, test)
