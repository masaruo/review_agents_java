.DEFAULT_GOAL := help
PYTHON := uv run python

# ────────────────────────────────────────────
# セットアップ
# ────────────────────────────────────────────

.PHONY: all
all: sync  ## 初回セットアップ（sync と同じ）

.PHONY: sync
sync:  ## 依存パッケージを lockfile に従ってインストール（開発用含む）
	uv sync --all-groups

.PHONY: install
install:  ## 本番依存のみインストール（dev グループ除く）
	uv sync --no-dev

# ────────────────────────────────────────────
# 実行
# ────────────────────────────────────────────

.PHONY: run
run:  ## レビュー実行（例: make run TARGET=/path/to/java-project）
ifndef TARGET
	$(error TARGET が指定されていません。例: make run TARGET=/path/to/java-project)
endif
	uv run java-review $(TARGET)

.PHONY: run-config
run-config:  ## 設定ファイルを指定してレビュー実行（例: make run-config TARGET=/path CONFIG=./config.yaml）
ifndef TARGET
	$(error TARGET が指定されていません)
endif
ifndef CONFIG
	$(error CONFIG が指定されていません)
endif
	uv run java-review $(TARGET) --config $(CONFIG)

# ────────────────────────────────────────────
# テスト
# ────────────────────────────────────────────

.PHONY: test
test:  ## 全テストを実行
	uv run pytest tests/ -v

.PHONY: test-unit
test-unit:  ## 単体テストのみ実行
	uv run pytest tests/unit/ -v

.PHONY: test-integration
test-integration:  ## 統合テストのみ実行（Ollama 不要・モック使用）
	uv run pytest tests/integration/ -v

.PHONY: test-cov
test-cov:  ## カバレッジ付きでテストを実行
	uv run pytest tests/ --cov=src/java_review_agent --cov-report=term-missing

# ────────────────────────────────────────────
# コード品質
# ────────────────────────────────────────────

.PHONY: lint
lint:  ## ruff で静的解析
	uv run ruff check src/ tests/

.PHONY: fmt
fmt:  ## ruff で自動フォーマット
	uv run ruff format src/ tests/

.PHONY: fmt-check
fmt-check:  ## フォーマットの確認のみ（変更しない）
	uv run ruff format --check src/ tests/

.PHONY: typecheck
typecheck:  ## mypy で型チェック
	uv run mypy src/

.PHONY: check
check: lint fmt-check typecheck  ## lint + フォーマット確認 + 型チェックをまとめて実行

# ────────────────────────────────────────────
# クリーンアップ
# ────────────────────────────────────────────

.PHONY: clean
clean:  ## キャッシュ・ビルド成果物を削除
	find . -type d -name __pycache__ | xargs rm -rf
	find . -type d -name .pytest_cache | xargs rm -rf
	find . -type d -name .mypy_cache  | xargs rm -rf
	find . -type d -name .ruff_cache  | xargs rm -rf
	find . -type d -name "*.egg-info" | xargs rm -rf
	find . -type d -name dist         | xargs rm -rf
	find . -type d -name build        | xargs rm -rf

.PHONY: clean-output
clean-output:  ## review_output/ 以下のレポートを削除
	rm -f review_output/*.md

.PHONY: clean-all
clean-all: clean clean-output  ## キャッシュ＋レポート出力をまとめて削除

# ────────────────────────────────────────────
# ユーティリティ
# ────────────────────────────────────────────

.PHONY: ollama-check
ollama-check:  ## Ollama の起動状態を確認
	curl -sf http://localhost:11434/api/tags > /dev/null \
		&& echo "Ollama: running" \
		|| echo "Ollama: not running (run 'ollama serve')"

.PHONY: ollama-pull
ollama-pull:  ## qwen2.5-coder:7b モデルをダウンロード
	ollama pull qwen2.5-coder:7b

.PHONY: env
env:  ## .env.example を .env にコピー（既存の .env は上書きしない）
	@test -f .env && echo ".env already exists, skipping." || cp .env.example .env && echo "Created .env from .env.example"

.PHONY: help
help:  ## このヘルプを表示
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
