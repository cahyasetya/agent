.PHONY: help lint format install setup clean test lint-flake8 lint-black lint-isort

help:
	@echo "Available commands:"
	@echo "  make setup     : Set up the project (install dependencies and pre-commit hook)"
	@echo "  make install   : Install dependencies"
	@echo "  make lint      : Run all linters (flake8, black, isort)"
	@echo "  make format    : Format code using black and isort"
	@echo "  make test      : Run tests"
	@echo "  make clean     : Clean up cache files"

lint: lint-flake8 lint-black lint-isort
	@echo "All linting checks passed!"

format:
	@echo "Formatting code with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .
	@echo "Formatting complete!"

lint-flake8:
	@echo "Running flake8..."
	flake8 .

lint-black:
	@echo "Checking code style with black..."
	black --check .

lint-isort:
	@echo "Checking import sorting with isort..."
	isort --check .

# Complete project setup
setup: install
	@echo "Setting up pre-commit hook..."
	@if [ -d ".git" ]; then \
		mkdir -p .git/hooks; \
		cp -f pre-commit.sample .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "Pre-commit hook installed."; \
	else \
		echo "No .git directory found. Initialize git first with 'git init'."; \
	fi
	@echo "Project setup complete!"

# Install dependencies
install: requirements.txt
	@echo "Installing dependencies..."
	pip install -r requirements.txt



# Run tests (placeholder for when you add tests)
test:
	@echo "Running tests..."
	pytest

# Clean up cache files
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
