# buildyoursmartcart.com - Development Commands

.PHONY: help install test lint format clean run dev build

help:  ## Show this help message
	@echo "buildyoursmartcart.com - Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install development dependencies
	pip install -e ".[dev,test]"

test:  ## Run all tests
	pytest

test-unit:  ## Run unit tests only
	pytest tests/unit -v

test-integration:  ## Run integration tests only
	pytest tests/integration -v

test-e2e:  ## Run end-to-end tests only
	pytest tests/e2e -v

test-coverage:  ## Run tests with coverage report
	pytest --cov=src --cov-report=html --cov-report=term

lint:  ## Run code linting
	flake8 src tests
	mypy src

format:  ## Format code with black and isort
	black src tests
	isort src tests

format-check:  ## Check code formatting
	black --check src tests
	isort --check-only src tests

clean:  ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage_html/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run:  ## Run the application in development mode
	cd src && python backend/main.py

dev:  ## Run the application with auto-reload
	cd src && uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload

build:  ## Build the application
	python -m build

docker-build:  ## Build Docker image
	docker build -t buildyoursmartcart:latest .

docker-run:  ## Run Docker container
	docker run -p 8080:8080 --env-file backend/.env buildyoursmartcart:latest

security-scan:  ## Run security validation
	python validate_security.py

validate:  ## Run all validation checks
	make format-check
	make lint
	make test
	make security-scan

# Production commands
deploy-staging:  ## Deploy to staging environment
	@echo "Deploying to staging..."
	# Add staging deployment commands

deploy-prod:  ## Deploy to production
	@echo "Deploying to production..."
	# Add production deployment commands

backup-db:  ## Backup production database
	@echo "Creating database backup..."
	# Add database backup commands