.PHONY: test test-unit test-integration test-verbose install clean

# Run all tests
test:
	pytest tests/ -v

# Run only unit tests (exclude integration marker)
test-unit:
	pytest tests/ -v -m "not integration"

# Run only integration tests
test-integration:
	pytest tests/ -v -m "integration"

# Run tests with verbose output and show print statements
test-verbose:
	pytest tests/ -vv -s

# Run tests with coverage report
test-coverage:
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html

# Install dependencies
install:
	pip install -r requirements.txt

# Clean up Python cache files and test artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# Run tests on file changes (requires pytest-watch)
watch:
	ptw tests/ -- -v

# Help command
help:
	@echo "Available make targets:"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run only unit tests"
	@echo "  make test-integration  - Run only integration tests"
	@echo "  make test-verbose      - Run tests with verbose output"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo "  make install           - Install Python dependencies"
	@echo "  make clean             - Clean up cache files and artifacts"
	@echo "  make watch             - Run tests on file changes"
