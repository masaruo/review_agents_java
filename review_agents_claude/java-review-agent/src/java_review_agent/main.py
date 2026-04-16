"""エントリポイント — CLIからプロジェクトディレクトリを受け取り、レビューを実行する"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from java_review_agent.backends.ollama import check_ollama_connection
from java_review_agent.config import load_config
from java_review_agent.graph import build_graph
from java_review_agent.schemas.models import (
    AgentNameType,
    DEFAULT_AGENTS,
    ReviewInstruction,
)
from java_review_agent.state import initial_state

_AGENT_MENU: list[tuple[AgentNameType, str, bool]] = [
    ("bug_detector", "Bug Detector", True),
    ("security_scanner", "Security Scanner", True),
    ("efficiency_analyzer", "Efficiency Analyzer", False),
    ("design_critic", "Design Critic", False),
    ("style_reviewer", "Style Reviewer", False),
]


def _prompt_review_instruction() -> ReviewInstruction:
    """対話的にレビュー指示を受け取り ReviewInstruction を返す"""
    print()
    print("=" * 50)
    print("  Java Code Review Agent")
    print("=" * 50)

    # Step 1: スコープ選択
    print()
    print("What would you like to review?")
    print("  1. Full review (all files)")
    print('  2. Specific file(s)  [e.g. "UserService.java"]')
    print('  3. Specific class    [e.g. "UserService"]')
    print('  4. Specific function [e.g. "authenticate"]')
    scope_map = {"1": "full", "2": "file", "3": "class", "4": "function"}

    while True:
        choice = input("Choice [1-4] (default: 1): ").strip() or "1"
        if choice in scope_map:
            scope = scope_map[choice]
            break
        print("  Invalid choice. Please enter 1-4.")

    scope_target: str | None = None
    if scope != "full":
        label = {"file": "filename", "class": "class name", "function": "function name"}[scope]
        while True:
            scope_target = input(f"Enter {label}: ").strip()
            if scope_target:
                break
            print(f"  {label} cannot be empty.")

    # Step 2: エージェント選択
    print()
    print("Which agents should run? (press Enter to keep defaults: bug, security)")
    for i, (name, label, default) in enumerate(_AGENT_MENU, start=1):
        status = "ON " if default else "OFF"
        print(f"  [{i}] {label:<25} (default: {status})")

    toggle_input = input("Enter numbers to toggle (e.g. '3 4'), or press Enter: ").strip()
    enabled: list[bool] = [default for _, _, default in _AGENT_MENU]
    if toggle_input:
        for token in toggle_input.split():
            if token.isdigit():
                idx = int(token) - 1
                if 0 <= idx < len(_AGENT_MENU):
                    enabled[idx] = not enabled[idx]

    enabled_agents: list[AgentNameType] = [
        name for (name, _, _), on in zip(_AGENT_MENU, enabled) if on
    ]
    if not enabled_agents:
        print("  No agents selected. Using defaults.")
        enabled_agents = list(DEFAULT_AGENTS)

    # Step 3: フォーカス質問（任意）
    print()
    focus_question = input(
        "Any specific question or focus? (optional, press Enter to skip)\n> "
    ).strip() or None

    print()
    return ReviewInstruction(
        scope=scope,  # type: ignore[arg-type]
        scope_target=scope_target,
        enabled_agents=enabled_agents,
        focus_question=focus_question,
    )


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
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="インタラクティブプロンプトをスキップし、全ファイル・全デフォルトエージェントで実行する",
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

    # インタラクティブ指示の取得
    if args.no_interactive:
        instruction = ReviewInstruction()
    else:
        instruction = _prompt_review_instruction()

    # グラフ構築・実行
    app = build_graph(config)
    state = initial_state(
        project_dir=project_dir,
        config=config,
        review_instruction=instruction,
    )

    final_state = app.invoke(state)

    if final_state.get("fatal_error"):
        print(f"[ERROR] {final_state['fatal_error']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
