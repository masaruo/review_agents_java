# CLAUDE.md — Java Code Q&A RAG Agent プロジェクトルール

このファイルはプロジェクトの開発ルールを定義するステアリングファイルである。
Claude Codeは実装の節目ごとにこのファイルを参照し、要件から外れていないか自己チェックすること。

---

## 開発ルール

### 基本方針

1. **SPEC駆動開発を徹底すること**
   - `spec/` ディレクトリ以下の仕様書に従って実装する
   - SPECに定義されていない機能をいきなり実装してはならない
   - SPECに書いてあることは必ず実装する

2. **テスト駆動開発（TDD）で進めること**
   - テストを先に書き、テストが通るように実装する
   - テストが失敗する理由を理解してから実装に進む

3. **型ヒントを全コードに付与すること**
   - 全関数・クラスのシグネチャに型ヒントを付与する
   - `typing` モジュールおよび `pydantic` を活用する
   - `mypy --strict` でエラーゼロを目標とする

4. **パッケージ管理は `uv` を使用すること**
   - `pip` の直接使用は容認しない
   - 依存関係は `pyproject.toml` で管理する
   - 仮想環境の作成・依存解決・スクリプト実行はすべて `uv` 経由で行う
   ```bash
   uv sync          # 依存関係のインストール
   uv run pytest    # テスト実行
   uv run ruff check src/  # lint
   ```

5. **コード品質ツールを使用すること**
   - `ruff` によるlintとフォーマットを維持する
   - `mypy` による型チェックをパスすること

6. **エラーが出たら自分でデバッグすること**
   - スタックトレースを読んで原因を特定する
   - 修正後は必ずテストを実行して確認する

7. **要件に関して不明点がある場合は、必ずユーザーに質問すること**
   - 推測で実装しない

8. **日本語で応答すること**
   - コードのコメントやdocstringは日本語でも英語でも可
   - ユーザーへの応答は日本語で行う

---

## SPEC修正ルール（バイブコーディング防止）

ユーザーから修正指示があった場合、いきなりコードを修正してはならない。
**必ず以下の手順を踏むこと：**

1. まず **SPEC を修正する**（`spec/` 以下の該当ファイルを更新）
2. 修正した SPEC をユーザーに提示し、以下のメッセージとともに確認する：
   ```
   SPECシートを修正しました。確認してください。OKであれば実装します。
   ```
3. ユーザーからOKを得てから、SPECに従って実装する

**この手順の省略は容認しない。**

---

## 環境変数管理ルール

- 認証情報や機密設定は `.env` ファイルで管理し、`python-dotenv` で読み込む
- `.env` は `.gitignore` に追加し、リポジトリにコミットしない
- `.env.example` を作成し、必要な変数名と説明を記載する
- `config.yaml` の値は環境変数で上書き可能とする（`.env` → `config.yaml` の優先順位）

---

## ステアリング（方向維持）

- この CLAUDE.md の内容をステアリングファイルとして、最後まで参照し続けること
- 要件から外れていないか、実装の節目ごとに自己チェックすること
- コンテキストが長くなったら自分で整理すること
- 実装前に `spec/` ディレクトリを確認し、仕様を把握してから実装に着手すること

---

## アーキテクチャ概要

```
src/java_qa_agent/
├── cli.py              # typer CLIエントリポイント
├── indexer.py          # FileScanner + JavaChunker + Indexer
├── retriever.py        # ChromaDB検索・top_k取得
├── context_builder.py  # コンテキスト結合・トークン制御
├── chat_session.py     # マルチターン対話ループ
├── project_manager.py  # プロジェクト管理CRUD
├── logger.py           # セッションログ保存
├── config.py           # config.yaml読み込み・シングルトン
├── backends/
│   ├── ollama_llm.py   # LLMバックエンド（抽象IF + Ollama実装）
│   └── ollama_embed.py # エンベディングバックエンド（抽象IF + Ollama実装）
└── schemas/
    └── models.py       # Pydanticモデル定義
```

---

## 重要制約

| 項目 | 制約 |
|------|------|
| Python | 3.10以上 |
| パッケージ管理 | `uv` のみ（`pip` 直接使用禁止） |
| LLMバックエンド | Ollama + qwen2.5-coder:7b |
| エンベディング | Ollama + nomic-embed-text |
| ベクトルDB | ChromaDB（ローカル永続化） |
| CLIフレームワーク | typer |
| データバリデーション | pydantic v2 |
| 並列実行 | Ollamaへの推論はシリアル実行（Max Concurrency: 1） |
| インデックス更新 | 全件削除・全件再挿入（差分更新なし） |

---

## テスト実行コマンド

```bash
# 全テスト実行
make test

# 特定のテストのみ
uv run pytest tests/unit/test_schemas.py -v

# lint
make lint

# 型チェック
make typecheck

# フォーマット
make format
```

---

## 参照ファイル一覧

| ファイル | 内容 |
|----------|------|
| `youken.md` | 要件定義書（確定要件の原本） |
| `spec/architecture.md` | 全体アーキテクチャ・データフロー |
| `spec/components.md` | 各コンポーネント詳細仕様 |
| `spec/prompts.md` | プロンプトテンプレート |
| `spec/schemas.md` | Pydanticモデル定義 |
| `spec/cli.md` | CLIサブコマンド仕様 |
| `spec/test-plan.md` | テスト計画・テストケース一覧 |
| `config.yaml` | 実行時設定ファイル |
| `.env.example` | 環境変数テンプレート |
