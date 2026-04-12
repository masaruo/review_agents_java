# アーキテクチャ仕様書

## システム概要

Java Code Q&A RAG Agentは、Javaプロジェクトのソースコードをベクトルデータベースにインデックス化し、自然言語による対話型質問応答を提供するシステムである。

### 主な用途
- バグ発見・修正提案
- リファクタリング提案
- セキュリティ評価
- 設計相談
- 汎用コード質問

---

## コンポーネント役割分担

| コンポーネント | モジュール | 役割 |
|---------------|-----------|------|
| FileScanner | `indexer.py` | srcディレクトリを再帰スキャンして .java ファイルを収集 |
| JavaChunker | `indexer.py` | Javaソースをメソッド単位に分割し、メタデータを付与 |
| Indexer | `indexer.py` | スキャン→チャンキング→エンベディング→ChromaDB保存を統括 |
| Retriever | `retriever.py` | ChromaDBから類似チャンクを検索し、top_k件を返却 |
| ContextBuilder | `context_builder.py` | チャンク+履歴+質問を結合し、トークン上限を制御 |
| ChatSession | `chat_session.py` | マルチターン対話ループを管理 |
| ProjectManager | `project_manager.py` | プロジェクト登録・切り替え・削除・一覧 |
| SessionLogger | `logger.py` | セッションログをJSONLファイルに保存 |
| OllamaLLM | `backends/ollama_llm.py` | Ollama推論バックエンド（抽象IF + 実装） |
| OllamaEmbedding | `backends/ollama_embed.py` | Ollamaエンベディングバックエンド（抽象IF + 実装） |
| AppConfig | `config.py` | config.yaml読み込み・環境変数マージ・シングルトン提供 |

---

## データフロー図

### インデックス構築フロー

```
make index project=<name> path=<dir>
         │
         ▼
    [CLI: cli.py]
    java-qa index --project <name> --path <dir>
         │
         ▼
    [ProjectManager]
    プロジェクト登録 → ~/.java_qa_agent/projects.json 更新
         │
         ▼
    [FileScanner]
    <dir>/src/ を再帰スキャン → .java ファイルリスト
         │
         ▼
    [JavaChunker]
    各ファイルをパース
    ├─ トークン数 < chunk_token_threshold (1000) → ファイル全体を1チャンク
    └─ トークン数 >= chunk_token_threshold      → メソッド単位に分割
    max_embed_tokens (768) を超えるチャンクはスライディングウィンドウで分割（overlap=200）
    ※768はtiktoken/BERT WordPieceのトークナイザー差異（最大2倍）を考慮した保守的な値
    メタデータ付与: imports, class_signature, member_vars
         │
         ▼
    [OllamaEmbedding]
    チャンクリストをバッチエンベディング
    nomic-embed-text → ベクトルリスト
         │
         ▼
    [ChromaDB]
    ~/.java_qa_agent/indexes/<project_name>/ に永続化
    （既存コレクションは全削除後に再挿入）
```

### 質問応答フロー

```
make chat project=<name>
         │
         ▼
    [CLI: cli.py]
    java-qa chat --project <name>
         │
         ▼
    [ChatSession.start()]
    ┌─ Ollama接続確認 → 失敗時は即時終了（STDERR出力）
    ├─ モデル存在確認 → 未取得時は STDERR に ollama pull コマンドを出力して終了
    └─ インデックス存在確認 → 未構築時は make index コマンドを提示して終了
         │
         ▼
    ┌────────────────────────────────┐
    │  対話ループ（ChatSession）      │
    │                                │
    │  [ユーザー入力]                 │
    │       │                        │
    │       ▼                        │
    │  [Retriever]                   │
    │  質問文をエンベディング          │
    │  ChromaDBから top_k 件取得      │
    │       │                        │
    │       ▼                        │
    │  [ContextBuilder]              │
    │  チャンク + 履歴 + 質問を結合   │
    │  max_input_tokens を超えないよう│
    │  古い履歴から切り詰め            │
    │       │                        │
    │       ▼                        │
    │  [OllamaLLM]                   │
    │  qwen2.5-coder:7b で回答生成   │
    │  シリアル実行（Max Concurrency 1)│
    │       │                        │
    │       ▼                        │
    │  [STDOUT] Markdown形式で出力    │
    │       │                        │
    │       ▼                        │
    │  [SessionLogger]               │
    │  ~/.java_qa_agent/logs/        │
    │  {project_name}/{timestamp}.jsonl │
    │       │                        │
    │       ▼                        │
    │  [ChatHistory更新]              │
    │  max_history_turns ターン保持   │
    │       │                        │
    │  "exit" or "quit" → ループ終了 │
    └────────────────────────────────┘
```

---

## ディレクトリ構成

```
~/.java_qa_agent/
├── projects.json              # プロジェクトレジストリ
├── indexes/
│   ├── {project_name}/        # ChromaDB永続化ディレクトリ（プロジェクトごと）
│   └── ...
└── logs/
    ├── {project_name}/
    │   ├── {timestamp}.jsonl  # セッションログ（JSONL形式）
    │   └── ...
    └── ...
```

---

## 技術スタック

| 用途 | ライブラリ | バージョン要件 |
|------|-----------|--------------|
| RAGオーケストレーション | langchain-community | >=0.3.0 |
| ベクトルDB | chromadb | >=0.5.0 |
| LLM・エンベディング | ollama（Python SDK） | >=0.3.0 |
| CLIフレームワーク | typer | >=0.12.0 |
| データバリデーション | pydantic | >=2.0.0（v2系） |
| 設定管理 | pyyaml | >=6.0 |
| 環境変数 | python-dotenv | >=1.0.0 |
| トークンカウント | tiktoken | >=0.7.0 |
| パッケージ管理 | uv | 最新安定版 |
| lint/format | ruff | >=0.4.0 |
| 型チェック | mypy | >=1.8.0 |
| テスト | pytest, pytest-asyncio | >=8.0.0 |

---

## 設計原則

### 単一責任の原則
各コンポーネントは明確に1つの責務を持つ。FileScanner はファイル収集のみ、JavaChunker は分割のみ、など。

### 抽象インタフェース
LLMバックエンドとエンベディングバックエンドは抽象インタフェース（ABC / Protocol）経由で呼び出す。
将来的なモデル・DBバックエンドの差し替えを容易にする。

### シリアル実行
Ollamaへの推論リクエストはシリアル実行（Max Concurrency: 1）とする。6GB VRAM制約に対応するため。

### バッチエンベディング
インデックス構築時のエンベディングはバッチで処理し、Ollamaへのリクエスト回数を最小化する。

### 全件再構築
インデックス更新は差分更新ではなく全件削除・全件再挿入とする。実装の単純さを優先する。
