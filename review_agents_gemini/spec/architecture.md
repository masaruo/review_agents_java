# Architecture Specification

## 1. システム概要
本システムは、Java ソースコードを解析し、複数の専門エージェント（LLM）を用いてコードレビューを自動化するツールである。LangGraph をオーケストレーション層として使用し、ローカル LLM (Ollama: `qwen2.5-coder:7b`) を用いて推論を行う。

## 2. 全体構成
システムは以下のコンポーネントで構成される：

- **CLI / Entrypoint**: ユーザーからのディレクトリ入力を受け取り、処理を開始する。
    - 追加引数 `--files`: 特定のファイル名またはパス（複数可）を指定。
    - 追加引数 `--instruction`: 全エージェントに共通で与える追加のレビュー指示（カスタムプロンプト）。
- **Configuration Management**: `config.yaml` から設定を読み込む。
- **File Scanner**: 指定されたディレクトリから `.java` ファイルを再帰的にスキャンする。`--files` が指定されている場合はそのファイルのみに限定する。
- **Orchestrator (LangGraph)**: レビュープロセスの状態（State）を管理し、各ノード（エージェント）を呼び出す。
- **Agents**: 
    - **Preprocessor**: コードを解析し、必要に応じてメソッド単位のスロットに分割。`--instruction` 内に関数名（メソッド名）への言及がある場合、または特定の関数指定がある場合は、該当するメソッドのみを抽出。
    - **Review Agents**: Bug Detector, Security Scanner, Efficiency Analyzer, Design Critic, Style Reviewer.
- **Output Generators**: 
    - **File Report Generator**: ファイルごとの Markdown レポート生成。
    - **Summary Generator**: 全体のサマリーレポート生成。

## 3. データフロー
1. **入力**: プロジェクトディレクトリのパス、ターゲットファイル（任意）、追加指示（任意）。
2. **スキャン**: `.java` ファイルの一覧を取得。`--files` が指定されている場合はそのファイルのみに限定する。
3. **ループ処理 (各ファイルごと)**:
    - **Preprocessor**: コードを解析。指示に基づいて特定のメソッドのみを抽出することも可能。
    - **Review Loop (各スロットごと)**:
        - 各専門エージェントがシリアルに推論を実行。ユーザーからの追加指示をプロンプトに組み込む。

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
