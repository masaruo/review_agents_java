"""FileScanner — src/ 配下の .java ファイルを再帰スキャンする"""

from __future__ import annotations

import sys
from pathlib import Path


def scan_java_files(project_dir: str) -> list[str]:
    """
    指定プロジェクトディレクトリの src/ 配下を再帰スキャンし、
    .java ファイルの絶対パス一覧をソートして返す。

    Args:
        project_dir: プロジェクトルートディレクトリのパス

    Returns:
        .java ファイルの絶対パス一覧（ソート済み）
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

    return java_files
