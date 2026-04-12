.PHONY: help install index chat list delete test lint format typecheck clean

# デフォルトターゲット
.DEFAULT_GOAL := help

##@ ヘルプ

help: ## 利用可能なターゲットの一覧と説明を表示
	@echo "Java Q&A RAG Agent - 利用可能なコマンド"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "使い方:\n  make \033[36m<ターゲット>\033[0m\n\nターゲット一覧:\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ セットアップ

install: ## 依存関係のインストール（uv sync）
	uv sync

##@ インデックス管理

index: ## 指定プロジェクトのインデックスを構築（make index project=<name> path=<dir>）
ifndef project
	$(error projectを指定してください: make index project=<name> path=<dir>)
endif
ifndef path
	$(error pathを指定してください: make index project=<name> path=<dir>)
endif
	uv run java-qa index --project $(project) --path $(path)

chat: ## 指定プロジェクトの対話セッションを開始（make chat project=<name>）
ifndef project
	$(error projectを指定してください: make chat project=<name>)
endif
	uv run java-qa chat --project $(project)

list: ## 登録済みプロジェクトの一覧を表示
	uv run java-qa list

delete: ## 指定プロジェクトのインデックスを削除（make delete project=<name>）
ifndef project
	$(error projectを指定してください: make delete project=<name>)
endif
	uv run java-qa delete --project $(project)

##@ 開発・テスト

test: ## テストスイート全体を実行（uv run pytest）
	uv run pytest tests/ -v

test-unit: ## ユニットテストのみ実行
	uv run pytest tests/unit/ -v

test-integration: ## 統合テストのみ実行
	uv run pytest tests/integration/ -v

test-cov: ## カバレッジ付きでテストを実行
	uv run pytest tests/ --cov=src/java_qa_agent --cov-report=term-missing -v

lint: ## ruff check によるlint実行
	uv run ruff check src/ tests/

format: ## ruff format によるフォーマット実行
	uv run ruff format src/ tests/

format-check: ## フォーマットチェック（変更なし）
	uv run ruff format --check src/ tests/

typecheck: ## mypy による型チェック実行
	uv run mypy src/

##@ クリーンアップ

clean: ## __pycache__ 等の生成物を削除
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "クリーンアップ完了"
