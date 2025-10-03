.PHONY: help install install-uv install-poetry test test-cov lint format clean docs

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies (auto-detect uv or poetry)
	@if command -v uv >/dev/null 2>&1; then \
		echo "Installing with uv..."; \
		uv sync --all-extras; \
	elif command -v poetry >/dev/null 2>&1; then \
		echo "Installing with poetry..."; \
		poetry install --with dev; \
	else \
		echo "Error: Neither uv nor poetry found. Please install one of them."; \
		exit 1; \
	fi

install-uv: ## Install dependencies with uv
	uv sync --all-extras

install-poetry: ## Install dependencies with poetry
	poetry install --with dev

test: ## Run tests
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest; \
	else \
		poetry run pytest; \
	fi

test-cov: ## Run tests with coverage report
	@if command -v uv >/dev/null 2>&1; then \
		uv run pytest --cov=baygon --cov-report=html --cov-report=term; \
	else \
		poetry run pytest --cov=baygon --cov-report=html --cov-report=term; \
	fi

lint: ## Run linters (ruff and black)
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff check baygon tests; \
		uv run black --check baygon tests; \
	else \
		poetry run ruff check baygon tests; \
		poetry run black --check baygon tests; \
	fi

format: ## Format code with ruff and black
	@if command -v uv >/dev/null 2>&1; then \
		uv run ruff check --fix baygon tests; \
		uv run ruff format baygon tests; \
		uv run black baygon tests; \
	else \
		poetry run ruff check --fix baygon tests; \
		poetry run ruff format baygon tests; \
		poetry run black baygon tests; \
	fi

tox: ## Run all tox environments
	@if command -v uv >/dev/null 2>&1; then \
		uv run tox; \
	else \
		poetry run tox; \
	fi

docs: ## Build documentation
	@if command -v uv >/dev/null 2>&1; then \
		uv run mkdocs build; \
	else \
		poetry run mkdocs build; \
	fi

clean: ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .tox/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
