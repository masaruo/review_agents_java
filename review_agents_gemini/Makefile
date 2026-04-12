# Variables
PYTHONPATH := src
UV := uv
PYTHON := python3
APP_MAIN := src/java_review_agent/main.py
OUTPUT_DIR := review_output

.PHONY: help all sync clean test lint typecheck run

help:
	@echo "Usage:"
	@echo "  make sync       - Dependencies synchronization using uv"
	@echo "  make test       - Run pytest"
	@echo "  make lint       - Run ruff check"
	@echo "  make typecheck  - Run mypy check"
	@echo "  make all        - Run sync, lint, typecheck and test"
	@echo "  make clean      - Remove venv, cache and output files"
	@echo "  make run DIR=.. - Run the review agent (e.g., make run DIR=src/)"

all: sync lint typecheck test

sync:
	$(UV) sync

test:
	export PYTHONPATH=$(PYTHONPATH) && $(UV) run pytest

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run mypy src

clean:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf $(OUTPUT_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +

run:
	@if [ -z "$(DIR)" ]; then \
		echo "Error: DIR variable is required. Example: make run DIR=tests/fixtures/sample_java"; \
		exit 1; \
	fi
	export PYTHONPATH=$(PYTHONPATH) && $(UV) run $(PYTHON) $(APP_MAIN) $(DIR)
