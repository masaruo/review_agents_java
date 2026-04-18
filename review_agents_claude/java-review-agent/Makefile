.DEFAULT_GOAL := help
PYTHON := uv run python

# ────────────────────────────────────────────
# Setup
# ────────────────────────────────────────────

.PHONY: all
all: sync  ## Initial setup (same as sync)

.PHONY: sync
sync:  ## Install all dependencies including dev (from lockfile)
	uv sync --all-groups

.PHONY: install
install:  ## Install production dependencies only (no dev)
	uv sync --no-dev

# ────────────────────────────────────────────
# Run
# ────────────────────────────────────────────

.PHONY: run
run:  ## Interactive CLI review  e.g. make run TARGET=/path/to/java-project
ifndef TARGET
	$(error TARGET is required. e.g. make run TARGET=/path/to/java-project)
endif
	uv run java-review $(TARGET)

.PHONY: run-full
run-full:  ## Non-interactive full review  e.g. make run-full TARGET=/path
ifndef TARGET
	$(error TARGET is required)
endif
	uv run java-review $(TARGET) --no-interactive

.PHONY: run-config
run-config:  ## Review with custom config  e.g. make run-config TARGET=/path CONFIG=./config.yaml
ifndef TARGET
	$(error TARGET is required)
endif
ifndef CONFIG
	$(error CONFIG is required)
endif
	uv run java-review $(TARGET) --config $(CONFIG)

.PHONY: serve
serve:  ## Start Web UI server at http://localhost:8000
	uv run uvicorn java_review_agent.server:app --host 0.0.0.0 --port 8000

.PHONY: serve-reload
serve-reload:  ## Start Web UI server with hot-reload (dev mode)
	uv run uvicorn java_review_agent.server:app --host 0.0.0.0 --port 8000 --reload

# ────────────────────────────────────────────
# Test
# ────────────────────────────────────────────

.PHONY: test
test:  ## Run all tests
	uv run pytest tests/ -v

.PHONY: test-unit
test-unit:  ## Run unit tests only
	uv run pytest tests/unit/ -v

.PHONY: test-integration
test-integration:  ## Run integration tests only (no Ollama required)
	uv run pytest tests/integration/ -v

.PHONY: test-cov
test-cov:  ## Run tests with coverage report
	uv run pytest tests/ --cov=src/java_review_agent --cov-report=term-missing

# ────────────────────────────────────────────
# Code quality
# ────────────────────────────────────────────

.PHONY: lint
lint:  ## Run ruff linter
	uv run ruff check src/ tests/

.PHONY: fmt
fmt:  ## Auto-format with ruff (modifies files)
	uv run ruff format src/ tests/

.PHONY: fmt-check
fmt-check:  ## Check formatting only (no changes)
	uv run ruff format --check src/ tests/

.PHONY: typecheck
typecheck:  ## Run mypy type checker
	uv run mypy src/

.PHONY: check
check: lint fmt-check typecheck  ## Run lint + fmt-check + typecheck (CI)

# ────────────────────────────────────────────
# Cleanup
# ────────────────────────────────────────────

.PHONY: clean
clean:  ## Remove cache and build artifacts
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name .pytest_cache | xargs rm -rf
	find . -type d -name .mypy_cache  | xargs rm -rf
	find . -type d -name .ruff_cache  | xargs rm -rf
	find . -type d -name "*.egg-info" | xargs rm -rf
	find . -type d -name dist         | xargs rm -rf
	find . -type d -name build        | xargs rm -rf

.PHONY: clean-output
clean-output:  ## Remove generated reports in review_output/
	rm -f review_output/*.md

.PHONY: clean-all
clean-all: clean clean-output  ## Remove cache and reports together

# ────────────────────────────────────────────
# Ollama utilities
# ────────────────────────────────────────────

.PHONY: ollama-check
ollama-check:  ## Check if Ollama is running
	curl -sf http://localhost:11434/api/tags > /dev/null \
		&& echo "Ollama: running" \
		|| echo "Ollama: not running (run 'ollama serve')"

.PHONY: ollama-pull
ollama-pull:  ## Download qwen2.5-coder:7b model (~4.7GB)
	ollama pull qwen2.5-coder:7b

.PHONY: env
env:  ## Copy .env.example to .env (skips if .env already exists)
	@test -f .env && echo ".env already exists, skipping." || cp .env.example .env && echo "Created .env from .env.example"

.PHONY: help
help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'
