"""FileScanner — src/ 配下の .java ファイルを再帰スキャンする"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from java_review_agent.schemas.models import ReviewInstruction


def scan_java_files(
    project_dir: str,
    instruction: Optional[ReviewInstruction] = None,
) -> list[str]:
    """
    指定プロジェクトディレクトリの src/ 配下を再帰スキャンし、
    .java ファイルの絶対パス一覧をソートして返す。
    instruction が指定された場合はスコープに応じてフィルタリングする。

    Args:
        project_dir: プロジェクトルートディレクトリのパス
        instruction: インタラクティブ指示（Noneの場合は全ファイルを返す）

    Returns:
        .java ファイルの絶対パス一覧（ソート済み・フィルタ済み）
    """
    src_dir = Path(project_dir) / "src"

    if not src_dir.exists():
        print(
            f"[WARNING] src/ directory not found: {src_dir}",
            file=sys.stderr,
        )
        return []

    java_files = sorted(str(p.resolve()) for p in src_dir.rglob("*.java"))

    if not java_files:
        print(
            f"[WARNING] No .java files found under: {src_dir}",
            file=sys.stderr,
        )
        return []

    if instruction is not None and instruction.scope_target:
        target = instruction.scope_target
        if instruction.scope == "file":
            java_files = [p for p in java_files if target in Path(p).name]
        elif instruction.scope == "class":
            java_files = [p for p in java_files if target in Path(p).stem]
        # "function" スコープはスロット単位フィルタのためここでは絞らない

        if not java_files:
            print(
                f"[WARNING] No .java files matched scope '{instruction.scope}': {target}",
                file=sys.stderr,
            )

    return java_files
