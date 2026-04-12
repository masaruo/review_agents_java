# Java Code Q&A RAG Agent

Java プロジェクトのソースコードをベクトル DB にインデックス化し、自然言語による対話型質問応答を提供する RAG エージェントです。

## 前提条件

- Python 3.10 以上
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.ai/)
  - 推論モデル: `ollama pull qwen2.5-coder:7b`
  - エンベディングモデル: `ollama pull nomic-embed-text`

## セットアップ手順

1. リポジトリをクローン
2. 依存関係のインストール:
   ```bash
   make install
   ```
3. Ollama が起動していることを確認

## 使い方

### インデックスの構築
```bash
make index project=my-project path=/path/to/java/project
```

### 対話セッションの開始
```bash
make chat project=my-project
```

### プロジェクト一覧の表示
```bash
make list
```

### プロジェクトの削除
```bash
make delete project=my-project
```

## Make ターゲット一覧

| ターゲット | 内容 |
|---|---|
| `make install` | 依存関係のインストール |
| `make index project=<name> path=<dir>` | 指定プロジェクトのインデックスを構築 |
| `make chat project=<name>` | 指定プロジェクトの対話セッションを開始 |
| `make list` | 登録済みプロジェクトの一覧を表示 |
| `make delete project=<name>` | 指定プロジェクトのインデックスを削除 |
| `make test` | テストを実行 |
| `make lint` | Lint チェック |
| `make format` | コードフォーマット |
| `make typecheck` | 型チェック |
| `make clean` | 一時ファイルの削除 |

## 設定

`config.yaml` で以下の項目を設定可能です：
- `java_version`: 対象とする Java のバージョン
- `ollama`: Ollama の接続先と使用モデル
- `rag`: top_k, トークン制限等の RAG パラメータ
- `storage`: インデックスとログの保存先

## プロジェクト構成

```
.
├── GEMINI.md               # プロジェクトルール
├── Makefile                # タスクランナー
├── pyproject.toml          # 依存関係管理 (uv)
├── config.yaml             # アプリケーション設定
├── spec/                   # 詳細仕様書
├── src/
│   └── java_qa_agent/      # ソースコード
└── tests/                  # テストコード
```
