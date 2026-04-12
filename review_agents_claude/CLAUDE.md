# CLAUDE.md — Java Code Review AI Agent

## プロジェクト概要

LangGraph + Ollama (`qwen2.5-coder:7b`) を使用したJavaコードレビューAIエージェントシステム。

---

## 開発ルール

- **SPEC駆動開発**：`spec/` ディレクトリの仕様書を作成し、それに従って実装すること
- **TDD**：テストを先に書き、テストが通るように実装すること
- **型ヒント**：全関数・クラスに `typing` / `pydantic` による型ヒントを付与すること
- **自己デバッグ**：エラーが出たら自分でデバッグすること
- **質問**：要件に関して不明点がある場合は、必ずユーザーに質問すること
- **応答言語**：日本語で応答すること

---

## SPEC修正ルール（バイブコーディング防止）

ユーザーから修正指示があった場合、いきなりコードを修正してはならない。
必ず以下の手順を踏むこと：

1. まず **SPEC を修正する**
2. 修正した SPEC をユーザーに提示し、「SPECシートを修正しました。確認してください。OKであれば実装します。」と確認する
3. ユーザーからOKを得てから、SPECに従って実装する

この手順の省略は容認しない。

---

## 環境変数管理ルール

- 認証情報は `.env` ファイルで管理し、`python-dotenv` で読み込むこと
- `.env` は `.gitignore` に追加し、リポジトリにコミットしないこと
- `.env.example` を作成し、必要な変数名と説明を記載すること

---

## ステアリング（方向維持）

- この `CLAUDE.md` の内容をステアリングファイルとして、最後まで参照し続けること
- 要件から外れていないか、実装の節目ごとに自己チェックすること
- コンテキストが長くなったら自分で整理すること

---

## アーキテクチャ概要

- **オーケストレーション**：LangGraph
- **LLMバックエンド**：Ollama (`qwen2.5-coder:7b`)
- **エージェント構成**：Preprocessor / Bug Detector / Security Scanner / Efficiency Analyzer / Design Critic / Style Reviewer / Aggregator / File Report Generator / Summary Generator
- **シリアル実行**：Ollamaへの推論リクエストはデフォルトMax Concurrency 1

---

## 技術スタック

| 用途 | ライブラリ / ツール |
|---|---|
| オーケストレーション | `langgraph` |
| LLMインタフェース | `langchain-community` |
| ローカルLLM | `ollama` (Python SDK) |
| データバリデーション | `pydantic` v2 |
| 設定管理 | `pyyaml` |
| テスト | `pytest`, `pytest-asyncio` |
| コード品質 | `ruff` |
| 型チェック | `mypy` |

---

## ディレクトリ構成

```
java-review-agent/
├── CLAUDE.md
├── youken.md
├── pyproject.toml
├── config.yaml
├── .env.example
├── .gitignore
├── spec/
│   ├── architecture.md
│   ├── agents.md
│   ├── prompts.md
│   ├── schemas.md
│   └── test-plan.md
├── src/
│   └── java_review_agent/
│       ├── __init__.py
│       ├── main.py
│       ├── graph.py
│       ├── state.py
│       ├── agents/
│       ├── backends/
│       ├── schemas/
│       ├── scanner.py
│       └── config.py
├── review_output/
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
        └── sample_java/
```
