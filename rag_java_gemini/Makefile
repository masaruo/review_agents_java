.PHONY: install index chat list delete test lint format typecheck clean help

install:
	uv sync

index:
	uv run java-qa index --project $(project) --path $(path)

chat:
	uv run java-qa chat --project $(project)

list:
	uv run java-qa list

delete:
	uv run java-qa delete --project $(project)

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy .

clean:
	rm -rf `find . -type d -name "__pycache__"`
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache

help:
	@echo "Usage:"
	@echo "  make install                - Install dependencies"
	@echo "  make index project=<name> path=<dir> - Index a project"
	@echo "  make chat project=<name>    - Start a chat session"
	@echo "  make list                   - List projects"
	@echo "  make delete project=<name>  - Delete a project index"
	@echo "  make test                   - Run tests"
	@echo "  make lint                   - Run linting"
	@echo "  make format                 - Run formatting"
	@echo "  make typecheck              - Run type checking"
	@echo "  make clean                  - Remove build artifacts"
