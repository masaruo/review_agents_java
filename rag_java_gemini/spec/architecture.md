# SPEC: アーキテクチャ (architecture.md)

## 1. システム概要
JavaソースコードをベクトルDB（ChromaDB）にインデックス化し、Ollama経由で推論モデル（qwen2.5-coder:7b）とエンベディングモデル（nomic-embed-text）を用いて自然言語による質問応答を行うRAGエージェント。

## 2. コンポーネント構成

### 2.1. インデックス構築（Indexer）
- **FileScanner**: `src/` 配下の `.java` ファイルを再帰的に収集。
- **Chunker**: `.java` ファイルをメソッド単位で分割。メタデータ（インポート、クラスシグネチャ等）を付与。
- **Embedder**: Ollama (`nomic-embed-text`) を使用してチャンクをベクトル化（バッチ処理）。
- **Vector DB**: ChromaDB を使用してローカル（`~/.java_qa_agent/indexes/{project_name}/`）に永続化。

### 2.2. 質問応答（Chat Engine）
- **Retriever**: ChromaDB から類似チャンクを `top_k` 件取得。
- **Context Builder**: 取得したチャンク、会話履歴、ユーザーの質問を統合。トークン制限（`max_input_tokens`）を遵守。
- **Generator**: Ollama (`qwen2.5-coder:7b`) を使用して回答を生成。
- **Session Manager**: 会話履歴（`max_history_turns`）を管理し、マルチターン対話を実現。

### 2.3. プロジェクト管理（Project Manager）
- プロジェクトの登録、一覧表示、削除、切り替えを担当。
- インデックスとログのディレクトリ管理。

## 3. データフロー

### 3.1. インデックス構築フロー
1. CLIコマンド実行: `make index project=<name> path=<dir>`
2. `ProjectManager` がパスを確認し、ディレクトリを準備。
3. `FileScanner` が対象ディレクトリから `.java` ファイルを抽出。
4. `Chunker` がファイルをメソッド単位に分割し、コンテキスト情報を抽出。
5. `Embedder` がチャンクをバッチ処理でベクトル化。
6. `ChromaDB` にベクトルとメタデータを保存。

### 3.2. チャットフロー
1. CLIコマンド実行: `make chat project=<name>`
2. `ProjectManager` がインデックスの存在を確認。
3. 対話ループ開始。
4. ユーザー入力を `Embedder` でベクトル化。
5. `Retriever` が類似チャンクを取得。
6. `ContextBuilder` がプロンプトを作成（履歴含む、トークン制限内）。
7. `Generator` (Ollama) が回答を生成。
8. 回答を表示し、ログに保存。

## 4. 外部依存関係
- **Ollama**: 推論およびエンベディングサーバ。
- **ChromaDB**: ベクトルデータベース。
- **LangChain**: RAGパイプラインのオーケストレーション。
