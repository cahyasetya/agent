.PHONY: run install clean build dist package install-package dev install-agent

run:
	python main.py $(ARGS)

run-focused:
	python main.py --path $(PATH) $(ARGS)

load-conversation:
	python main.py --load $(CONV) $(ARGS)

install:
	pip install -r requirements.txt

# Install the agent with proper checks
install-agent:
	@echo "Checking if agent is already installed..."
	@if pip list | grep -q "ai-agent"; then \
		echo "Uninstalling existing agent package..."; \
		pip uninstall -y ai-agent; \
	fi
	@echo "Installing agent package..."
	pip install -e .
	@echo "Installation complete. Try running 'agent' to verify."

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/

# Build the package
build:
	python -m pip install --upgrade pip
	python -m pip install --upgrade build
	python -m build

# Create source and wheel distributions
dist: clean
	python -m pip install --upgrade pip
	python -m pip install --upgrade build wheel
	python -m build

# Install the package in development mode
dev:
	pip install -e .

# Install the package from the built distributions
install-package: dist
	pip install dist/*.whl
