PHONY: install test lint format clean build publish

# Install dependencies
install:
	pip install -e ".[dev]"
	playwright install

# Run tests
test:
	pytest tests/ -v

# Run linting
lint:
	flake8 src/
	mypy src/

# Format code
format:
	black src/ tests/
	isort src/ tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build package
build: clean
	python -m build

# Publish to PyPI
publish: build
	python -m twine upload dist/*

# Run development server
dev:
	python -m playwright_mcp.cli --headless

# Install playwright browsers
install-browsers:
	playwright install

# Run type checking
typecheck:
	mypy src/

# Docker related commands
docker-build:
	docker build -t playwright-mcp-python .

docker-run:
	docker run -it --rm playwright-mcp-python

# Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 playwright && \
    chown -R playwright:playwright /app
USER playwright

# Expose port (if running HTTP server)
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["playwright-mcp-python"]
CMD ["--headless", "--browser=chromium"]

# requirements.txt
mcp>=1.0.0
playwright>=1.40.0
pydantic>=2.0.0

# requirements-dev.txt
-r requirements.txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
mypy>=1.0.0
flake8>=6.0.0
isort>=5.12.0
twine>=4.0.0
build>=0.10.0