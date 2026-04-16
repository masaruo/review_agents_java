"""Summary Generator — プロジェクト全体サマリーの生成"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from java_review_agent.backends.ollama import OllamaBackend
from java_review_agent.schemas.models import FileReport, ReviewIssue, SkippedItem

_PRIORITY_LABELS = {
    1: "P1 バグ",
    2: "P2 セキュリティ",
    3: "P3 効率性",
    4: "P4 設計",
    5: "P5 可読性",
}

_PROMPT_TEMPLATE = """\
You are an expert Java {java_version} software architect performing a holistic code review.

Below is a summary of issues found across all files in the project:

{issues_summary}

Based on these findings, provide a comprehensive project-level analysis covering:
1. Overall architecture assessment (module dependencies, data flow, architectural recommendations)
2. Most critical systemic issues that appear across multiple files
3. Patterns of problems (e.g., "security issues are concentrated in the data access layer")
4. Top 3-5 priority recommendations for the development team

Java Version: {java_version}
Total files reviewed: {total_files}
Total issues found: {total_issues}

Respond in Japanese Markdown format. Be concise and actionable.
"""


def _build_issues_summary(file_reports: list[FileReport]) -> str:
    """全ファイルの問題一覧テキストを生成する"""
    lines: list[str] = []
    for report in file_reports:
        file_name = Path(report.file_path).name
        lines.append(f"## {file_name} ({report.issue_count}件)")
        # レポートの内容から問題部分を抜粋（簡易）
        lines.append(report.content[:500] + ("..." if len(report.content) > 500 else ""))
        lines.append("")
    return "\n".join(lines)


def _count_by_priority(file_reports: list[FileReport]) -> dict[int, int]:
    """優先度別の問題数を集計する（レポートの issue_count のみ使用）"""
    # ファイルレポートには issue_count しかないため、ここでは簡易集計
    return {}


class SummaryGeneratorAgent:
    def __init__(self, backend: OllamaBackend) -> None:
        self.backend = backend

    def generate(
        self,
        file_reports: list[FileReport],
        skipped_items: list[SkippedItem],
        java_version: int,
        project_dir: str,
        output_dir: str,
        focus_question: str | None = None,
    ) -> str:
        """
        全ファイルのレビュー結果をもとにサマリーレポートを生成する。

        Returns:
            生成されたMarkdown文字列
        """
        now = datetime.now(tz=timezone.utc).isoformat()
        total_files = len(file_reports)
        total_issues = sum(r.issue_count for r in file_reports)
        issues_summary = _build_issues_summary(file_reports)

        focus_section = (
            f"\n\nUser's specific question/focus:\n{focus_question}"
            if focus_question
            else ""
        )
        prompt = _PROMPT_TEMPLATE.format(
            java_version=java_version,
            issues_summary=issues_summary,
            total_files=total_files,
            total_issues=total_issues,
        ) + focus_section

        try:
            llm_analysis = self.backend.generate(prompt)
        except Exception as exc:
            llm_analysis = f"（サマリー生成中にエラーが発生しました: {exc}）"

        # スキップ一覧テーブル
        skip_section = ""
        if skipped_items:
            rows = "\n".join(
                f"| {item.target} | {item.reason} | {item.detail} |"
                for item in skipped_items
            )
            skip_section = (
                "\n## スキップされたファイル/メソッド一覧\n\n"
                "| 対象 | 理由 | 詳細 |\n"
                "|---|---|---|\n"
                f"{rows}\n"
            )

        # 優先度別サマリー（簡易）
        priority_rows = "\n".join(
            f"| {label} | {total_issues if p == 1 else '-'} |"
            for p, label in _PRIORITY_LABELS.items()
        )

        content = (
            f"# Java Code Review Summary\n\n"
            f"**プロジェクト**: {project_dir}\n"
            f"**Java Version**: {java_version}\n"
            f"**レビュー日時**: {now}\n"
            f"**処理ファイル数**: {total_files}件\n"
            f"**スキップ数**: {len(skipped_items)}件\n\n"
            f"---\n\n"
            f"## アーキテクチャ評価\n\n"
            f"{llm_analysis}\n"
            f"{skip_section}"
        )

        # ファイル保存
        summary_path = str(Path(output_dir) / "summary.md")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(summary_path).write_text(content, encoding="utf-8")

        # STDOUT 出力
        print(content)
        sys.stdout.flush()

        return content
