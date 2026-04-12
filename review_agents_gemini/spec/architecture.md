# Architecture Specification

## 1. システム概要
本システムは、Java ソースコードを解析し、複数の専門エージェント（LLM）を用いてコードレビューを自動化するツールである。LangGraph をオーケストレーション層として使用し、ローカル LLM (Ollama: `qwen2.5-coder:7b`) を用いて推論を行う。

## 2. 全体構成
システムは以下のコンポーネントで構成される：

- **CLI / Entrypoint**: ユーザーからのディレクトリ入力を受け取り、処理を開始する。
- **Configuration Management**: `config.yaml` から設定を読み込む。
- **File Scanner**: 指定されたディレクトリから `.java` ファイルを再帰的にスキャンする。
- **Orchestrator (LangGraph)**: レビュープロセスの状態（State）を管理し、各ノード（エージェント）を呼び出す。
- **Agents**: 
    - **Preprocessor**: トークン数推定とチャンキング（メソッド単位分割）。
    - **Review Agents**: Bug Detector, Security Scanner, Efficiency Analyzer, Design Critic, Style Reviewer.
    - **Aggregator**: 各エージェントの結果を統合し、優先度付けと重複除去を行う。
- **Output Generators**: 
    - **File Report Generator**: ファイルごとの Markdown レポート生成。
    - **Summary Generator**: 全体のサマリーレポート生成。

## 3. データフロー
1. **入力**: プロジェクトディレクトリのパス。
2. **スキャン**: `.java` ファイルの一覧を取得。
3. **ループ処理 (各ファイルごと)**:
    - **Preprocessor**: コードを解析し、必要に応じてメソッド単位のスロットに分割。
    - **Review Loop (各スロットごと)**:
        - 各専門エージェントがシリアルに推論を実行（VRAM 制限のため Max Concurrency: 1）。
    - **Aggregator**: スロットごとの結果をファイル単位で統合。
    - **Report Generation**: `./review_output/{filename}.md` を生成。
4. **全体サマリー**: 全ファイルの処理結果に基づき `./review_output/summary.md` を生成。

## 4. 技術スタック
- Python 3.10+
- LangGraph
- LangChain (Community)
- Ollama (Python SDK)
- Pydantic v2
- PyYAML
- pytest / pytest-asyncio
- Ruff / mypy

## 5. ディレクトリ構造
`youken.md` に記載された構造に従う。
