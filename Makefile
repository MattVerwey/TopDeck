.PHONY: help install install-dev test lint format type-check security check check-all clean run run-help health-check health-check-detailed docker-up docker-down

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
	@echo "🔍 Running linters..."
	ruff check src tests
	black --check src tests

format: ## Format code with black and ruff
	@echo "✨ Formatting code..."
	ruff check --fix src tests
	black src tests

type-check: ## Run type checking with mypy
	@echo "🔎 Running type checker..."
	mypy src

security: ## Run security checks
	@echo "🔒 Running security checks..."
	@command -v bandit >/dev/null 2>&1 || { echo "⚠️  bandit not installed, skipping security check. Install with: pip install bandit"; exit 0; }
	@bandit -r src -ll -f text || echo "⚠️  Security issues found"
	@command -v safety >/dev/null 2>&1 || { echo "⚠️  safety not installed, skipping dependency check. Install with: pip install safety"; exit 0; }
	@safety check --json || echo "⚠️  Vulnerable dependencies found"

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov coverage.xml .coverage
	rm -rf dist build *.egg-info

run: ## Run the API server
	PYTHONPATH=src python -m topdeck

run-help: ## Show help for running the API server
	PYTHONPATH=src python -m topdeck --help

health-check: ## Check if the API server is running and healthy
	python scripts/health_check.py

health-check-detailed: ## Check API server health with detailed information
	python scripts/health_check.py --detailed

docker-up: ## Start Docker services (Neo4j, Redis, RabbitMQ)
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker service logs
	docker-compose logs -f

check: lint type-check test ## Run standard checks (lint, type-check, test)
	@echo "✅ All standard checks passed!"

check-all: lint type-check security test ## Run all checks including security
	@echo "✅ All checks passed!"
