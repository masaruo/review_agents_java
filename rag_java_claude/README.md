# Java Code Q&A RAG Agent

JavaプロジェクトのソースコードをベクトルDBにインデックス化し、自然言語による対話型質問応答を提供するRAGエージェントです。

バグ発見・リファクタリング提案・セキュリティ評価・設計相談など、Javaコードに関する様々な質問に対して、ソースコードを参照した正確な回答を生成します。Ollama（ローカルLLM）を使用するため、コードがクラウドに送信されず、プライバシーを保ちながら利用できます。

---

## 前提条件

### Python・uv

```bash
# Python 3.10以上が必要
python --version

# uvのインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Ollama

```bash
# Ollamaのインストール（macOS）
brew install ollama

# Ollamaの起動
ollama serve

# 必要なモデルのダウンロード
ollama pull qwen2.5-coder:7b   # 推論モデル（約4GB）
ollama pull nomic-embed-text    # エンベディングモデル（約274MB）
```

---

## セットアップ手順

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd rag_java_claude

# 2. 依存関係のインストール
make install
# または: uv sync

# 3. 環境変数の設定（必要な場合）
cp .env.example .env
# .env を編集して必要な値を設定

# 4. Ollamaが起動していることを確認
ollama serve
```

---

## 使い方

### インデックス構築

JavaプロジェクトのソースコードをベクトルDBにインデックス化します。

```bash
# Makefileを使用
make index project=my-app path=/path/to/my-java-project

# またはCLIを直接使用
java-qa index --project my-app --path /path/to/my-java-project
```

### 対話セッション開始

```bash
# Makefileを使用
make chat project=my-app

# またはCLIを直接使用
java-qa chat --project my-app
```

セッション開始後：
```
Java Q&A Agent - プロジェクト: my-app
Ollama: qwen2.5-coder:7b
終了するには 'exit' または 'quit' を入力してください

質問を入力してください: addメソッドの実装を教えてください

[検索中...]

## 回答

`Calculator` クラスの `add` メソッドは...

質問を入力してください: それはスレッドセーフですか？

（会話の文脈を引き継いで回答）
```

### プロジェクトの切り替え

```bash
# 別のプロジェクトをインデックス化
make index project=another-app path=/path/to/another-project

# 別のプロジェクトに切り替えて対話
make chat project=another-app
```

### 登録済みプロジェクトの一覧表示

```bash
make list
# または: java-qa list
```

### プロジェクトの削除

```bash
make delete project=my-app
# または: java-qa delete --project my-app
```

---

## Makeターゲット一覧

| ターゲット | 説明 |
|-----------|------|
| `make install` | 依存関係のインストール（`uv sync`） |
| `make index project=<name> path=<dir>` | 指定プロジェクトのインデックスを構築 |
| `make chat project=<name>` | 指定プロジェクトの対話セッションを開始 |
| `make list` | 登録済みプロジェクトの一覧を表示 |
| `make delete project=<name>` | 指定プロジェクトのインデックスを削除 |
| `make test` | テストスイート全体を実行 |
| `make test-unit` | ユニットテストのみ実行 |
| `make test-integration` | 統合テストのみ実行 |
| `make test-cov` | カバレッジ付きでテストを実行 |
| `make lint` | `ruff check` によるlint実行 |
| `make format` | `ruff format` によるフォーマット実行 |
| `make typecheck` | `mypy` による型チェック実行 |
| `make clean` | `__pycache__` 等の生成物を削除 |
| `make help` | 利用可能なターゲットの一覧と説明を表示 |

---

## 設定

`config.yaml` で主要パラメータを設定できます。

```yaml
java_version: 17          # JavaバージョンをLLMプロンプトに埋め込む
ollama:
  base_url: "http://localhost:11434"   # OllamaサーバーのURL
  model: "qwen2.5-coder:7b"           # 推論モデル
  embed_model: "nomic-embed-text"     # エンベディングモデル
  timeout_seconds: 120                # タイムアウト（秒）
rag:
  top_k: 5                # 検索で取得するチャンク数
  chunk_token_threshold: 1000  # このトークン数未満はファイル全体をインデックス化
  max_input_tokens: 3000  # LLMへの最大入力トークン数
  max_history_turns: 6    # 保持する会話履歴のターン数
storage:
  index_dir: "~/.java_qa_agent/indexes"  # インデックス保存先
  log_dir: "~/.java_qa_agent/logs"       # ログ保存先
  save_logs: true                        # セッションログを保存するか
```

### 環境変数での上書き

`.env` ファイルで設定値を上書きできます：

```bash
cp .env.example .env
# .env を編集
OLLAMA_BASE_URL=http://remote-server:11434
```

---

## プロジェクト構成

```
rag_java_claude/
├── CLAUDE.md                    # 開発ルール・プロジェクトガイドライン
├── Makefile                     # タスクランナー
├── pyproject.toml               # 依存関係・ツール設定
├── config.yaml                  # アプリケーション設定
├── .env.example                 # 環境変数テンプレート
├── .gitignore
├── README.md
├── spec/                        # 仕様書
│   ├── architecture.md          # 全体アーキテクチャ・データフロー
│   ├── components.md            # 各コンポーネント詳細仕様
│   ├── prompts.md               # プロンプトテンプレート
│   ├── schemas.md               # Pydanticモデル定義
│   ├── cli.md                   # CLIサブコマンド仕様
│   └── test-plan.md             # テスト計画
├── src/
│   └── java_qa_agent/
│       ├── __init__.py
│       ├── cli.py               # typer CLIエントリポイント
│       ├── indexer.py           # FileScanner + JavaChunker + Indexer
│       ├── retriever.py         # ChromaDB検索・top_k取得
│       ├── context_builder.py   # コンテキスト結合・トークン制御
│       ├── chat_session.py      # マルチターン対話ループ
│       ├── project_manager.py   # プロジェクト管理CRUD
│       ├── logger.py            # セッションログ保存
│       ├── config.py            # config.yaml読み込み・シングルトン
│       ├── backends/
│       │   ├── __init__.py
│       │   ├── ollama_llm.py    # LLMバックエンド（抽象IF + Ollama実装）
│       │   └── ollama_embed.py  # エンベディングバックエンド（抽象IF + Ollama実装）
│       └── schemas/
│           ├── __init__.py
│           └── models.py        # Pydanticモデル定義
├── tests/
│   ├── unit/                    # ユニットテスト
│   ├── integration/             # 統合テスト
│   └── fixtures/
│       └── sample_java/         # テスト用Javaファイル
└── examples/
    └── qa_sample.py             # 使用例スクリプト
```

---

## データ保存先

```
~/.java_qa_agent/
├── projects.json              # プロジェクトレジストリ
├── indexes/
│   └── {project_name}/        # ChromaDB永続化ディレクトリ
└── logs/
    └── {project_name}/
        └── {timestamp}.jsonl  # セッションログ（JSONL形式）
```

---

## トラブルシューティング

### Ollamaに接続できない

```bash
# Ollamaを起動する
ollama serve

# 別のポートを使用する場合
OLLAMA_BASE_URL=http://localhost:11435 java-qa chat --project my-app
```

### モデルが見つからない

```bash
# モデルをダウンロードする
ollama pull qwen2.5-coder:7b
ollama pull nomic-embed-text
```

### インデックスが見つからない

```bash
# インデックスを構築する
make index project=my-app path=/path/to/project
```
