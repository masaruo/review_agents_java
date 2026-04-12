"""Aggregator — 全エージェント結果の統合・優先度付け・重複除去"""

from __future__ import annotations

from java_review_agent.schemas.models import AggregatedResult, AgentOutput, ReviewIssue, SkippedItem


def _dedup_issues(issues: list[ReviewIssue]) -> list[ReviewIssue]:
    """
    同一 (category, location, description) の問題を重複除去する。
    最初に出現したものを残す。
    """
    seen: set[tuple[str, str, str]] = set()
    result: list[ReviewIssue] = []
    for issue in issues:
        key = (issue.category, issue.location, issue.description)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def aggregate(
    agent_outputs: list[AgentOutput],
    file_path: str,
) -> tuple[AggregatedResult, list[SkippedItem]]:
    """
    複数エージェントの出力を集約し、優先度順・重複除去した AggregatedResult を返す。

    Args:
        agent_outputs: 全エージェントの AgentOutput リスト
        file_path: 対象ファイルパス

    Returns:
        (AggregatedResult, SkippedItem リスト)
    """
    all_issues: list[ReviewIssue] = []
    skipped_items: list[SkippedItem] = []

    for output in agent_outputs:
        if output.skipped:
            # スキップされたエージェントのSkippedItemはagent_outputsから再構築
            # （BaseReviewAgentでSkippedItemとして記録されるが、ここでも集約する）
            continue
        all_issues.extend(output.issues)

    # 優先度昇順ソート
    all_issues.sort(key=lambda x: x.priority)

    # 重複除去
    deduped = _dedup_issues(all_issues)

    return AggregatedResult(
        file_path=file_path,
        issues=deduped,
        skipped_items=skipped_items,
    ), skipped_items
