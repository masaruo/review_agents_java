# Java Code Review AI Agent

LangGraph + Ollama (`qwen2.5-coder:7b`) を使用したローカルLLMによるJavaコードレビューエージェントシステム。

---

## 目次

- [概要](#概要)
- [必要な環境](#必要な環境)
- [セットアップ](#セットアップ)
- [使い方](#使い方)
  - [Web UI（ブラウザ）](#web-uiブラウザ)
  - [CLI](#基本的な使い方インタラクティブ起動)
- [出力例](#出力例)
- [設定](#設定)
- [テストの実行](#テストの実行)
- [プロジェクト構成](#プロジェクト構成)
- [レビュー観点と優先度](#レビュー観点と優先度)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

指定したJavaプロジェクトの `src/` ディレクトリ配下を再帰的にスキャンし、5種類のAIエージェントがコードをレビューして Markdown レポートを生成します。

| エージェント | 役割 | 優先度 |
|---|---|---|
| Bug Detector | NullPointerException・リソースリーク・ロジックエラー等の検出 | P1 |
| Security Scanner | SQLインジェクション・機密情報露出等の脆弱性検出 | P2 |
| Efficiency Analyzer | アルゴリズム・データ構造・I/O効率の分析 | P3 |
| Design Critic | SOLID原則違反・設計パターン評価 | P4 |
| Style Reviewer | 可読性の大まかな評価（細かい規約違反の列挙はしない） | P5 |

---

## 必要な環境

- [uv](https://docs.astral.sh/uv/) （Pythonパッケージマネージャー）
- Python 3.10 以上（uv が自動管理）
- [Ollama](https://ollama.com/) がローカルで起動していること
- `qwen2.5-coder:7b` モデルがダウンロード済みであること

---

## セットアップ

### 1. uv のインストール

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# または Homebrew
brew install uv
```

### 2. Ollama のインストールとモデルの準備

```bash
# Ollama のインストール（公式サイト: https://ollama.com/ を参照）

# モデルのダウンロード（約4.7GB）
make ollama-pull

# Ollama サーバーの起動（別ターミナルで）
ollama serve
```

### 3. リポジトリのクローンと依存パッケージのインストール

```bash
git clone <repository-url>
cd java-review-agent

# 依存パッケージのインストール（仮想環境の作成も自動で行われる）
make sync
```

### 4. 環境変数の設定（任意）

```bash
make env
# 生成された .env を編集して必要に応じてエンドポイントやモデルを変更
```

---

## 使い方

### Web UI（ブラウザ）

ブラウザ上でレビューの設定・実行・追加質問をすべて行えます。

```bash
# Web UI サーバーを起動
make serve
```

`http://localhost:8000` をブラウザで開きます。

#### 操作フロー

1. **左ペイン**でプロジェクトディレクトリ・スコープ・エージェントを設定し「レビュー開始」をクリック
2. **右ペイン上段**にレビュー結果がタブ形式で表示される
3. **右ペイン下段**のチャット欄でレビュー結果に関する追加質問を入力

> 開発中はホットリロード付き `make serve-reload` が便利です。

---

### 基本的な使い方（インタラクティブ起動）

```bash
make run TARGET=/path/to/your/java-project
```

または `uv run` で直接実行：

```bash
uv run java-review /path/to/your/java-project
```

起動後、3ステップのプロンプトでレビュー方針を指定します。

```
==================================================
  Java Code Review Agent
==================================================

What would you like to review?
  1. Full review (all files)
  2. Specific file(s)  [e.g. "UserService.java"]
  3. Specific class    [e.g. "UserService"]
  4. Specific function [e.g. "authenticate"]
Choice [1-4] (default: 1): 3
Enter class name: UserService

Which agents should run? (press Enter to keep defaults: bug, security)
  [1] Bug Detector              (default: ON )
  [2] Security Scanner          (default: ON )
  [3] Efficiency Analyzer       (default: OFF)
  [4] Design Critic             (default: OFF)
  [5] Style Reviewer            (default: OFF)
Enter numbers to toggle (e.g. '3 4'), or press Enter:

Any specific question or focus? (optional, press Enter to skip)
> 認証フローの設計はどう思う？
```

| ステップ | 内容 | デフォルト |
|---|---|---|
| レビュースコープ | 全ファイル / 特定ファイル / クラス / メソッド | 全ファイル |
| 実行エージェント | 5つのエージェントからトグル選択 | Bug + Security のみ |
| フォーカス質問 | サマリーに追記される自由記述（任意） | なし |

**対象ディレクトリ**は `src/` を含むプロジェクトルートを指定します。

```
your-java-project/
└── src/               ← ここ以下の .java ファイルが対象
    └── com/
        └── example/
            ├── Main.java
            └── Service.java
```

### インタラクティブプロンプトをスキップして実行

```bash
# 全ファイル・デフォルトエージェント（bug + security）で即実行
make run-full TARGET=/path/to/java-project

# または直接
uv run java-review /path/to/java-project --no-interactive
```

### カスタム設定ファイルを指定する

```bash
make run-config TARGET=/path/to/java-project CONFIG=./config-production.yaml

# または直接
uv run java-review /path/to/java-project --config ./config-production.yaml
```

### 実行例

```bash
# インタラクティブ起動
make run TARGET=~/projects/my-spring-app

# 非インタラクティブで全ファイルレビュー
make run-full TARGET=~/projects/my-spring-app

# 別の設定ファイルを使用
make run-config TARGET=~/projects/my-spring-app CONFIG=./config-production.yaml
```

---

## 出力例

### ファイル単位レポート（`./review_output/{ファイル名}.md`）

```markdown
# Code Review Report: BuggyClass.java

**レビュー日時**: 2026-04-12T10:00:00+00:00
**対象ファイル**: /path/to/src/BuggyClass.java

---

## 検出された問題

### [P1 バグ検出]

#### 問題1
- **場所**: BuggyClass#getLength
- **重要度**: 🔴 critical
- **説明**: String引数に対するnullチェックがなく、NullPointerExceptionが発生する可能性があります
- **改善提案**: メソッドの先頭で `if (str == null) throw new IllegalArgumentException(...)` を追加してください

### [P2 セキュリティ]

#### 問題1
- **場所**: BuggyClass#readFile
- **重要度**: 🟠 major
- **説明**: FileInputStreamがtry-with-resourcesで管理されておらず、リソースリークが発生します
- **改善提案**: `try (FileInputStream fis = new FileInputStream(path)) { ... }` に書き直してください
```

### 全体サマリー（`./review_output/summary.md`）

プロジェクト全体のアーキテクチャ評価・問題のパターン分析・優先度の高い推奨事項・スキップされたファイル/メソッドの一覧を含むレポートが生成されます。

---

## 設定

`config.yaml` で動作をカスタマイズできます。

```yaml
# Java バージョン（プロンプトに反映される）
java_version: 17

# Ollama 設定
ollama:
  base_url: "http://localhost:11434"   # Ollama エンドポイント
  model: "qwen2.5-coder:7b"           # 使用モデル
  timeout_seconds: 120                 # タイムアウト（秒）

# 処理設定
processing:
  max_concurrency: 1          # 同時推論リクエスト数（VRAMに応じて調整）
  chunk_token_threshold: 1000 # これを超えるファイルはメソッド単位に分割
  max_input_tokens: 3000      # 各スロットの最大入力トークン数
  response_reserve_tokens: 1000

# 出力設定
output:
  dir: "./review_output"      # レポート出力先ディレクトリ
```

### 主要パラメータの説明

| パラメータ | 説明 | 推奨値 |
|---|---|---|
| `max_concurrency` | VRAM 6GB 環境では `1` を推奨。VRAM に余裕がある場合は増やせる | `1` |
| `chunk_token_threshold` | ファイルをメソッド単位に分割するトークン数の閾値 | `1000` |
| `max_input_tokens` | 各エージェントへの入力トークン上限。大きくすると精度向上するが速度低下 | `3000` |
| `timeout_seconds` | Ollama の推論タイムアウト。低スペックマシンでは大きくする | `120`〜`300` |

---

## テストの実行

```bash
# 全テストを実行
make test

# 単体テストのみ
make test-unit

# 統合テストのみ（Ollama不要・モック使用）
make test-integration

# カバレッジ付きで実行
make test-cov

# 特定ファイルを直接指定する場合
uv run pytest tests/unit/test_preprocessor.py -v
```

### テスト構成

| カテゴリ | テスト数 | 内容 |
|---|---|---|
| スキーマバリデーション | 14 | Pydanticモデルの入力検証 |
| 設定管理 | 4 | config.yaml 読み込み |
| FileScanner | 5 | .java ファイル再帰スキャン |
| Preprocessor / チャンキング / トークン制限 | 18 | メソッド分割・コンテキスト付与 |
| Aggregator | 6 | 結果統合・優先度ソート・重複除去 |
| レビューエージェント | 13 | 各エージェントの入出力・エラー処理 |
| Ollama通信 | 4 | 接続確認・推論リクエスト |
| LangGraph遷移 | 3 | グラフの状態遷移 |
| **合計** | **71** | |

---

## Makefile コマンド一覧

```bash
make help           # コマンド一覧を表示
```

| コマンド | 説明 |
|---|---|
| `make all` / `make sync` | 依存パッケージを lockfile に従いインストール（開発用含む） |
| `make install` | 本番依存のみインストール（dev グループ除く） |
| `make serve` | Web UI サーバーを起動（http://localhost:8000） |
| `make serve-reload` | Web UI サーバーを開発モード（ホットリロード）で起動 |
| `make run TARGET=<dir>` | インタラクティブ起動でレビューを実行 |
| `make run-full TARGET=<dir>` | プロンプトをスキップして全ファイル・デフォルトエージェントで実行 |
| `make run-config TARGET=<dir> CONFIG=<yaml>` | 設定ファイルを指定してレビューを実行 |
| `make test` | 全テストを実行 |
| `make test-unit` | 単体テストのみ実行 |
| `make test-integration` | 統合テストのみ実行（Ollama不要） |
| `make test-cov` | カバレッジ付きでテストを実行 |
| `make lint` | ruff で静的解析 |
| `make fmt` | ruff で自動フォーマット |
| `make fmt-check` | フォーマット確認のみ（変更しない） |
| `make typecheck` | mypy で型チェック |
| `make check` | lint + fmt-check + typecheck をまとめて実行 |
| `make clean` | キャッシュ・ビルド成果物を削除 |
| `make clean-output` | `review_output/` 以下のレポートを削除 |
| `make clean-all` | キャッシュ＋レポートをまとめて削除 |
| `make ollama-check` | Ollama の起動状態を確認 |
| `make ollama-pull` | `qwen2.5-coder:7b` をダウンロード |
| `make env` | `.env.example` を `.env` にコピー |

---

## プロジェクト構成

```
java-review-agent/
├── README.md
├── CLAUDE.md                          # 開発ルール
├── Makefile                           # タスクランナー（uv コマンド集）
├── pyproject.toml                     # 依存関係管理
├── config.yaml                        # 実行設定
├── .env.example                       # 環境変数テンプレート
├── spec/                              # 仕様書
│   ├── architecture.md               # 全体アーキテクチャ
│   ├── agents.md                     # エージェント詳細仕様
│   ├── prompts.md                    # プロンプトテンプレート
│   ├── schemas.md                    # Pydanticスキーマ定義
│   └── test-plan.md                  # テスト計画
├── static/
│   └── index.html                    # Web UI（シングルページ）
├── src/
│   └── java_review_agent/
│       ├── main.py                   # CLIエントリポイント
│       ├── server.py                 # FastAPI Web UIサーバー
│       ├── chat.py                   # 追加質問チャットハンドラ
│       ├── graph.py                  # LangGraphグラフ定義
│       ├── state.py                  # グラフ状態初期化
│       ├── scanner.py                # .java ファイルスキャン
│       ├── config.py                 # 設定ファイル読み込み
│       ├── agents/
│       │   ├── base.py               # 抽象基底エージェント
│       │   ├── preprocessor.py       # チャンキング・メタデータ抽出
│       │   ├── bug_detector.py       # バグ検出（P1）
│       │   ├── security_scanner.py   # セキュリティ（P2）
│       │   ├── efficiency_analyzer.py # 効率性（P3）
│       │   ├── design_critic.py      # 設計（P4）
│       │   ├── style_reviewer.py     # 可読性（P5）
│       │   ├── aggregator.py         # 結果統合
│       │   ├── file_report_generator.py
│       │   └── summary_generator.py
│       ├── backends/
│       │   └── ollama.py             # Ollamaバックエンド
│       └── schemas/
│           └── models.py             # Pydantic v2 モデル
├── review_output/                    # 生成されたレポートの出力先
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
        └── sample_java/              # テスト用Javaファイル
```

---

## レビュー観点と優先度

| 優先度 | 観点 | 主な検出内容 |
|---|---|---|
| P1 | バグ検出 | NullPointerException、リソースリーク、ロジックエラー、配列境界違反、スレッド安全性 |
| P2 | セキュリティ | SQLインジェクション、コマンドインジェクション、機密情報の露出、安全でない暗号化 |
| P3 | 効率性 | O(n²)アルゴリズム、不適切なデータ構造、ループ内DB呼び出し、不要なオブジェクト生成 |
| P4 | 設計 | SOLID原則違反、高結合・低凝集、テスタビリティの低さ |
| P5 | 可読性 | 不明瞭な命名、メソッドの過度な長さ、深いネスト（網羅的な列挙はしない） |

---

## トラブルシューティング

### `[ERROR] Failed to connect to Ollama.` が表示される

Ollamaが起動していないか、エンドポイントが異なります。

```bash
# Ollama を起動
ollama serve

# 起動確認
curl http://localhost:11434/api/tags
```

### 推論が非常に遅い / タイムアウトする

`config.yaml` の `timeout_seconds` を増やしてください。

```yaml
ollama:
  timeout_seconds: 300   # 5分に延長
```

### メモリ不足（OOM）エラーが発生する

`max_concurrency: 1`（デフォルト）であることを確認してください。他のGPUを使うアプリを終了し、Ollamaを再起動してください。

OOMが発生したスロットは `Skipped (Resource Limit)` として記録され、他のファイルのレビューは継続されます。スキャン全体は停止しません。

### `src/` ディレクトリが見つからない

指定するディレクトリは `src/` を含むプロジェクトルートである必要があります。

```bash
# 正しい例
java-review /path/to/my-project      # my-project/src/ が存在する

# 誤った例
java-review /path/to/my-project/src  # src/ を直接指定しない
```

### レビューがスキップされたファイルを確認したい

`./review_output/summary.md` の「スキップされたファイル/メソッド一覧」セクションに記載されています。
