# GEMINI.md - Java Code Review AI Agent

## プロジェクト概要
LangGraph と Ollama (`qwen2.5-coder:7b`) を使用した Java コードレビュー自動化エージェント。

## 開発ルール
- **SPEC駆動開発**: まず `spec/` ディレクトリ内に詳細仕様書を作成し、ユーザーの承認を得てから実装に進む。
- **TDD (Test-Driven Development)**: テストを先に書き、そのテストをパスするように実装を行う。
- **型ヒント**: すべての Python コードに型ヒント (`typing` / `pydantic`) を付与する。
- **エラーハンドリング**: エラー発生時は自己デバッグを行い、解決できない場合や要件に不明点がある場合はユーザーに質問する。
- **言語**: ユーザーへの応答およびドキュメントは日本語で行う。

## SPEC修正ルール（バイブコーディング防止）
ユーザーから修正指示があった場合、いきなりコードを修正せず以下の手順を踏むこと：
1. `spec/` 内の該当する仕様書を修正する。
2. 修正した仕様書をユーザーに提示し、「SPECシートを修正しました。確認してください。OKであれば実装します。」と確認する。
3. ユーザーの承認を得てから、仕様に従って実装を開始する。

## 環境変数管理
- 認証情報や設定は `.env` ファイルで管理し、`python-dotenv` で読み込む。
- `.env` は `.gitignore` に追加し、コミットしない。
- `.env.example` を作成し、必要な変数名を記載する。

## 技術スタック
- **言語**: Python 3.10+
- **パッケージ管理**: uv
- **オーケストレーション**: LangGraph
- **LLM**: Ollama (`qwen2.5-coder:7b`) via LangChain
- **バリデーション**: Pydantic v2
- **リンター/フォーマッタ**: Ruff
- **テスト**: pytest, pytest-asyncio

## エージェント構成
1. **Orchestrator**: グラフ全体の状態管理とルーティング。
2. **Preprocessor**: コード読み込み、トークン数推定、チャンキング。
3. **Review Agents**: Bug Detector, Security Scanner, Efficiency Analyzer, Design Critic, Style Reviewer.
4. **Aggregator**: 結果の統合、優先度付け、重複除去。
5. **Generators**: File Report Generator, Summary Generator.

## ステアリング
- 本 `GEMINI.md` の内容を常に参照し、プロジェクトの方向性を維持する。
- 実装の節目ごとに要件との整合性をセルフチェックする。
- コンテキストが肥大化した場合は適宜整理する。
