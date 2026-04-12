# Java Code Review AI Agent

LangGraph と Ollama (`qwen2.5-coder:7b`) を活用した、Java コード専用の自動レビューエージェントです。

## 特徴

- **マルチエージェント構成**: バグ検出、セキュリティ、効率性、設計、スタイルの 5 つの専門エージェントがコードを多角的に分析します。
- **LangGraph による制御**: エージェント間の状態管理とワークフローを最適化。
- **ローカル LLM 推論**: Ollama を使用し、プライベートな環境で高速に推論を実行します（シリアル実行制御により VRAM 消費を抑制）。
- **大規模ファイル対応**: 1,000 トークンを超えるファイルは、メソッド単位に自動分割（チャンキング）して処理。
- **優先度付きレポート**: 指摘事項を重要度順に集約・ソートし、重複を除去した Markdown レポートを生成。

## 動作要件

- **Python**: 3.10 以上
- **Ollama**: インストール済みで、`qwen2.5-coder:7b` モデルが利用可能であること
- **uv**: Python パッケージマネージャー

## セットアップ

### 1. Ollama の準備

Ollama を起動し、モデルをプルしておきます。

```bash
ollama pull qwen2.5-coder:7b
```

### 2. インストール

`uv` を使用して仮想環境の作成と依存関係のインストールを行います。

```bash
uv venv
uv pip install -e ".[dev]"
```

## 使い方

### レビューの実行

対象の Java プロジェクトが含まれるディレクトリを指定して実行します。

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uv run python3 src/java_review_agent/main.py <対象ディレクトリへのパス>
```

### 出力結果

レビュー結果は `./review_output/` ディレクトリに生成されます。

- `{ファイル名}.md`: 各ファイルごとの詳細レポート
- `summary.md`: プロジェクト全体のサマリーとスキップされた項目のログ

## 設定

`config.yaml` を編集することで、Java のバージョンや LLM のパラメータ、チャンキングの閾値を調整できます。

```yaml
java_version: 17
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5-coder:7b"
  timeout_seconds: 120
processing:
  max_concurrency: 1
  chunk_token_threshold: 1000  # この値を超えるとメソッド単位で分割
output:
  dir: "./review_output"
```

## 開発とテスト

### テストの実行

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src
uv run pytest
```

### 静的解析 (Lint/Type Check)

```bash
uv run ruff check .
uv run mypy src
```

## アーキテクチャ

1. **Scanner**: `.java` ファイルを再帰的に収集。
2. **Preprocessor**: トークン推定と必要に応じたメソッド分割。
3. **Reviewers**: 5 つのエージェントによるシリアル推論。
4. **Aggregator**: 重複除去と優先度ベースの統合。
5. **Generators**: レポートおよびサマリーの Markdown 出力。
