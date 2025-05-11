.PHONY: help lint format install setup clean test lint-flake8 lint-black lint-isort fix-pep8 fix-f541

help:
	@echo "Available commands:"
	@echo "  make setup     : Set up the project (install dependencies)"
	@echo "  make install   : Install dependencies"
	@echo "  make lint      : Run all linters (flake8, black, isort)"
	@echo "  make format    : Format code using black and isort"
	@echo "  make fix-pep8  : Fix PEP8 issues using autopep8"
	@echo "  make fix-f541  : Fix f-string missing placeholders"
	@echo "  make fix-lint  : Fix all linting issues at once"
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

fix-pep8:
	@echo "Installing autopep8 if needed..."
	pip install -q autopep8
	@echo "Fixing PEP8 issues with autopep8..."
	autopep8 --in-place --aggressive --aggressive --max-line-length=80 --recursive .
	@echo "Running flake8 to check remaining issues..."
	flake8 --output-file=.flake8_result_after.txt .
	@echo "Before: $$(grep -c "^" .flake8_result.txt) issues"
	@echo "After: $$(grep -c "^" .flake8_result_after.txt) issues"
	@echo "Fixed $$(expr $$(grep -c "^" .flake8_result.txt) - $$(grep -c "^" .flake8_result_after.txt)) issues"
	@echo "PEP8 fixing complete!"

fix-f541:
	@echo "Fixing f-string missing placeholders (F541)..."
	@python -c 'import re; import os; import sys; \
		def fix_f541(filepath): \
			with open(filepath, "r") as f: content = f.read(); \
			f_strings = re.finditer(r"f\"([^\"]*)\"|f\'([^\']*)\'", content); \
			fixed = content; \
			for match in f_strings: \
				if "{" not in match.group(0): \
					old = match.group(0); \
					new = old[0] + old[1:]; \
					fixed = fixed.replace(old, new); \
			if fixed != content: \
				with open(filepath, "w") as f: f.write(fixed); \
				print(f"Fixed F541 issues in {filepath}"); \
		for root, dirs, files in os.walk("."): \
			if "venv" in root or ".git" in root: continue; \
			for file in files: \
				if file.endswith(".py"): \
					fix_f541(os.path.join(root, file));'
	@echo "F541: f-string missing placeholders - fixed!"

fix-lint: fix-pep8 fix-f541
	@echo "All automatic lint fixes applied!"

lint-flake8:
	@echo "Running flake8, excluding virtual environment..."
	flake8 --output-file=.flake8_result_new.txt .
	@echo "Line too long (E501): $$(grep -c "E501" .flake8_result_new.txt)"
	@echo "F-string missing placeholders (F541): $$(grep -c "F541" .flake8_result_new.txt)"
	@echo "Trailing whitespace (W291): $$(grep -c "W291" .flake8_result_new.txt)"
	@echo "Blank line contains whitespace (W293): $$(grep -c "W293" .flake8_result_new.txt)"
	@echo "Total issues: $$(wc -l < .flake8_result_new.txt)"

lint-black:
	@echo "Checking code style with black..."
	black --check .

lint-isort:
	@echo "Checking import sorting with isort..."
	isort --check .

# Complete project setup
setup: install
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
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyd" -delete
	find . -type f -name "run_flake8.sh" -delete
	find . -type f -name "run_flake8_check.sh" -delete
	@echo "Clean complete!"
