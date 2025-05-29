.PHONY: install test lint format clean build publish dev docker-build docker-run

# Variables
POETRY := poetry

# Install dependencies and browsers
install:
	$(POETRY) install
	$(POETRY) run playwright install
	sudo apt-get update && sudo apt-get install -y libavif13 libwoff1 libharfbuzz-icu0

# Run tests (with browser check)
test: check-browsers
	$(POETRY) run pytest tests/ -v --tb=short

# Check if browsers are installed
check-browsers:
	@echo "Checking if Playwright browsers are installed..."
	@$(POETRY) run playwright --version > /dev/null 2>&1 || (echo "Installing Playwright browsers..." && $(POETRY) run playwright install)


# Format code
format:
	$(POETRY) run black --line-length 79 src/
	$(POETRY) run isort src/
	$(POETRY) run black --line-length 79 src/
	$(POETRY) run isort src/
	ruff format src/
	ruff check src/ --ignore D107 --fix --unsafe-fixes
	ruff format tests/
	ruff check tests/ --ignore D107 --fix --unsafe-fixes
	$(POETRY) run mypy tests/
	$(POETRY) run mypy src/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Build package
build: clean
	$(POETRY) build

# Publish to PyPI
publish: build
	$(POETRY) publish

# Run development server
dev:
	$(POETRY) run python -m playwright_mcp.cli --headless

# Install playwright browsers only
install-browsers:
	$(POETRY) run playwright install

# Install only chromium (faster for testing)
install-chromium:
	$(POETRY) run playwright install chromium

# Development helpers - install everything needed for development
dev-install: install

# Test with coverage
test-cov: check-browsers
	$(POETRY) run pytest tests/ -v --cov=src/playwright_mcp --cov-report=html --cov-report=term

# Quick setup for new developers
setup: install
	@echo "✅ Setup complete! Run 'make test' to run tests."

# Reinstall browsers (useful if browsers are corrupted)
reinstall-browsers:
	$(POETRY) run playwright uninstall
	$(POETRY) run playwright install