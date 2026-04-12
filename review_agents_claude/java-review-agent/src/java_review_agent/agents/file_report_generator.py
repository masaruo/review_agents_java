"""File Report Generator — ファイル単位Markdownレポートの生成"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from java_review_agent.schemas.models import AggregatedResult, FileReport, ReviewIssue

_PRIORITY_LABELS = {
    1: "P1 バグ検出",
    2: "P2 セキュリティ",
    3: "P3 効率性",
    4: "P4 設計",
    5: "P5 可読性",
}

_SEVERITY_EMOJI = {
    "critical": "🔴",
    "major": "🟠",
    "minor": "🟡",
    "info": "🔵",
}


def _render_issue(issue: ReviewIssue, index: int) -> str:
    severity_label = _SEVERITY_EMOJI.get(issue.severity, "") + " " + issue.severity
    return (
        f"#### 問題{index}\n"
        f"- **場所**: {issue.location}\n"
        f"- **重要度**: {severity_label}\n"
        f"- **説明**: {issue.description}\n"
        f"- **改善提案**: {issue.suggestion}\n"
    )


def generate_file_report(
    aggregated: AggregatedResult,
    output_dir: str,
) -> FileReport:
    """
    AggregatedResult から Markdown レポートを生成し、ファイルに保存してSTDOUTにも出力する。

    Args:
        aggregated: Aggregator の集約結果
        output_dir: 出力ディレクトリ

    Returns:
        FileReport
    """
    now = datetime.now(tz=timezone.utc).isoformat()
    file_name = Path(aggregated.file_path).stem
    report_path = str(Path(output_dir) / f"{file_name}.md")

    # 問題を優先度でグループ化
    grouped: dict[int, list[ReviewIssue]] = {}
    for issue in aggregated.issues:
        grouped.setdefault(issue.priority, []).append(issue)

    # Markdown 構築
    lines: list[str] = [
        f"# Code Review Report: {Path(aggregated.file_path).name}",
        "",
        f"**レビュー日時**: {now}",
        f"**対象ファイル**: {aggregated.file_path}",
        "",
        "---",
        "",
        "## 検出された問題",
        "",
    ]

    if not aggregated.issues:
        lines.append("問題は検出されませんでした。")
    else:
        for priority in sorted(grouped.keys()):
            label = _PRIORITY_LABELS.get(priority, f"P{priority}")
            lines.append(f"### [{label}]")
            lines.append("")
            for i, issue in enumerate(grouped[priority], start=1):
                lines.append(_render_issue(issue, i))

    # スキップ一覧
    if aggregated.skipped_items:
        lines += [
            "",
            "---",
            "",
            "## スキップされた項目",
            "",
            "| スロット/エージェント | 理由 | 詳細 |",
            "|---|---|---|",
        ]
        for item in aggregated.skipped_items:
            lines.append(f"| {item.target} | {item.reason} | {item.detail} |")

    content = "\n".join(lines) + "\n"

    # ディレクトリ作成（存在しない場合）
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # ファイル保存
    Path(report_path).write_text(content, encoding="utf-8")

    # STDOUT 出力
    print(content)
    sys.stdout.flush()

    return FileReport(
        file_path=aggregated.file_path,
        report_path=report_path,
        content=content,
        issue_count=len(aggregated.issues),
    )
