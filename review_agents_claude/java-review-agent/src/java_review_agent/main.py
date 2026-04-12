"""エントリポイント — CLIからプロジェクトディレクトリを受け取り、レビューを実行する"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from java_review_agent.backends.ollama import check_ollama_connection
from java_review_agent.config import load_config
from java_review_agent.graph import build_graph
from java_review_agent.state import initial_state


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Java Code Review AI Agent — LangGraph + Ollama"
    )
    parser.add_argument(
        "project_dir",
        type=str,
        help="レビュー対象のJavaプロジェクトディレクトリ（src/ を含むルートディレクトリ）",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="設定ファイルのパス（デフォルト: config.yaml）",
    )
    args = parser.parse_args()

    # プロジェクトディレクトリの存在確認
    project_dir = str(Path(args.project_dir).resolve())
    if not Path(project_dir).exists():
        print(f"[ERROR] Project directory not found: {project_dir}", file=sys.stderr)
        sys.exit(1)

    # 設定読み込み
    config = load_config(args.config)

    # Ollama 接続確認（失敗時は SystemExit）
    check_ollama_connection(
        base_url=config.ollama.base_url,
        model=config.ollama.model,
    )

    # グラフ構築・実行
    app = build_graph(config)
    state = initial_state(project_dir=project_dir, config=config)

    final_state = app.invoke(state)

    if final_state.get("fatal_error"):
        print(f"[ERROR] {final_state['fatal_error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
