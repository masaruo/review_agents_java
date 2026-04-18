# Java Code Review AI Agent

LangGraph と Ollama (`qwen2.5-coder:7b`) を活用した、Java コード専用の自動レビューエージェントです。

## 特徴

- **Web UI & Chat**: ブラウザ上でレビュー結果を確認し、AI と対話しながら修正案を相談可能。
- **マルチエージェント構成**: バグ検出、セキュリティ、効率性、設計、スタイルの 5 つの専門エージェントがコードを多角的に分析。
- **LangGraph による制御**: エージェント間の状態管理とワークフローを最適化。
- **ローカル LLM 推論**: Ollama を使用し、プライベートな環境で高速に推論を実行。
- **大規模ファイル対応**: トークン数に応じてメソッド単位に自動分割（チャンキング）して処理。
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

`uv` を使用して依存関係をインストールします。

```bash
make sync
```

## 使い方

### Web UI モード (推奨)

ブラウザ上でレビュー結果を確認し、AI と対話しながらコード修正の相談ができます。

```bash
make ui
```
起動後、ブラウザで `http://localhost:8501` にアクセスしてください。サイドバーから対象ディレクトリを指定して「Start Review」をクリックします。

### CLI モード

一括でレポートファイルを生成する場合に使用します。

```bash
make run DIR=<対象ディレクトリへのパス>
```

または直接スクリプトを実行します。

```bash
export PYTHONPATH=$(pwd)/src
uv run python3 src/java_review_agent/main.py <対象ディレクトリへのパス>
```

## 設定

`config.yaml` を編集することで、Java のバージョンや LLM のパラメータ、チャンキングの閾値を調整できます。

```yaml
java_version: 17
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5-coder:7b"
processing:
  max_concurrency: 1
  chunk_token_threshold: 1000  # この値を超えるとメソッド単位で分割
output:
  dir: "./review_output"
```

## 開発とテスト

### 便利コマンド (Makefile)

- `make sync`: 依存関係の同期
- `make test`: テストの実行
- `make lint`: Ruff による静的解析
- `make typecheck`: Mypy による型チェック
- `make clean`: キャッシュや出力ファイルの削除

## アーキテクチャ

1. **Scanner**: `.java` ファイルを再帰的に収集。
2. **Preprocessor**: トークン推定と必要に応じたメソッド分割。
3. **Reviewers**: 5 つのエージェントによるシリアル推論。
4. **Aggregator**: 重複除去と優先度ベースの統合。
5. **Generators**: レポートおよびサマリーの Markdown 出力。
6. **Web UI**: Streamlit によるブラウザインターフェースと対話機能。
