.PHONY: help install dev-install test lint format clean run-api run-bot docker-build docker-run

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync --no-dev

dev-install: ## Install development dependencies
	uv sync --dev
	uv run pre-commit install

test: ## Run tests
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	uv run pytest tests/ -v --cov=src/ --cov-report=html --cov-report=term

lint: ## Run linting tools
	uv run flake8 src/
	uv run mypy src/ --ignore-missing-imports
	uv run bandit -r src/

format: ## Format code
	uv run black src/ tests/
	uv run isort src/ tests/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

run-api: ## Run the trading bot API server
	uv run python main.py api

run-bot: ## Run the trading bot
	uv run python main.py bot

run-monitor: ## Run the monitoring dashboard
	uv run python monitor.py

backtest: ## Run backtesting
	uv run python main.py backtest

docker-build: ## Build Docker image
	docker build -t python-binance-trading-bot .

docker-run: ## Run Docker container
	docker-compose up -d

docker-stop: ## Stop Docker container
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f trading-bot

setup-env: ## Setup environment file from example
	cp .env.example .env
	@echo "Please edit .env file with your actual API keys"

pre-commit: ## Run pre-commit on all files
	uv run pre-commit run --all-files

upgrade-deps: ## Upgrade dependencies
	uv lock --upgrade

security-check: ## Run security checks
	uv run safety check
	uv run bandit -r src/

serve-docs: ## Serve documentation locally
	@echo "Starting documentation server..."
	@echo "Visit http://localhost:8080 to view docs"
	python -m http.server 8080 --directory docs/

init: dev-install setup-env ## Initialize development environment
	@echo "Development environment setup complete!"
	@echo "Don't forget to configure your .env file with API keys."
