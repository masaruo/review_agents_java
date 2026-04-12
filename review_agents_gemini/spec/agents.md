# Agents Specification

## 1. エージェント一覧

### Preprocessor
- **役割**: Java ソースコードを読み込み、トークン数を推定する。
- **チャンキング**: 1,000トークンを超える場合、メソッド単位に分割する。
- **コンテキスト付与**: 各スロットにインポート宣言、クラスシグネチャ、メンバ変数を付与する。
- **出力**: 1つ以上のチャンク（スロット）。

### Review Agents (共通仕様)
- **使用モデル**: `qwen2.5-coder:7b` (Ollama)
- **制約**: シリアル実行（Max Concurrency: 1）。
- **エラー処理**: 接続失敗や OOM 時は `Skipped (Resource Limit)` を記録し、スキャンを継続する。パース失敗時は `Skipped (Parse Error)` を記録する。

#### Bug Detector
- **役割**: バグやロジックエラー（NullPointerException, リソースリーク等）の検出。
- **優先度**: 1

#### Security Scanner
- **役割**: セキュリティ脆弱性（インジェクション、機密情報の露出等）の検出。
- **優先度**: 2

#### Efficiency Analyzer
- **役割**: 効率性（アルゴリズム、オブジェクト生成、I/O効率等）の分析。
- **優先度**: 3

#### Design Critic
- **役割**: 設計（SOLID 原則、デザインパターン）の評価。
- **優先度**: 4

#### Style Reviewer
- **役割**: 可読性やコーディング規約の大まかな評価。
- **優先度**: 5

### Aggregator
- **役割**: 全エージェントの結果を統合する。
- **処理**: 確定要件の優先度順に重み付けし、重複する指摘を除去する。

### File Report Generator
- **役割**: 各ファイルのレビュー結果を Markdown レポートとして出力する。
- **出力先**: `./review_output/{filename}.md`

### Summary Generator
- **役割**: プロジェクト全体の流れ、推奨事項、レビューがスキップされたファイル/メソッドの一覧を含むサマリーを生成する。
- **出力先**: `./review_output/summary.md`

## 2. 入出力スキーマ (詳細は schemas.md 参照)
各ノードは Pydantic モデルで定義された入出力を使用する。

## 3. シリアル実行の制御
LangGraph の `nodes` 内で Ollama への呼び出しを逐次的に行い、共有の推論リソースを占有しないよう制御する。
