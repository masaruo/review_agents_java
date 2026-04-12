"""AGG-xxx: Aggregatorテスト"""

from __future__ import annotations

import pytest

from java_review_agent.agents.aggregator import aggregate
from java_review_agent.schemas.models import AgentOutput, ReviewIssue, SkippedItem


def make_issue(priority: int, location: str = "Foo#bar", desc: str = "desc") -> ReviewIssue:
    cat = {1: "bug", 2: "security", 3: "efficiency", 4: "design", 5: "style"}[priority]
    return ReviewIssue(
        priority=priority,
        category=cat,
        severity="major",
        location=location,
        description=desc,
        suggestion="fix it",
    )


class TestAggregate:
    def test_agg001_sorted_by_priority(self) -> None:
        """AGG-001: 優先度順（1→5）にソートされる"""
        outputs = [
            AgentOutput(
                slot_id="f::m",
                agent_name="style_reviewer",
                issues=[make_issue(5)],
            ),
            AgentOutput(
                slot_id="f::m",
                agent_name="bug_detector",
                issues=[make_issue(1)],
            ),
            AgentOutput(
                slot_id="f::m",
                agent_name="security_scanner",
                issues=[make_issue(2)],
            ),
        ]
        result, _ = aggregate(outputs, "Foo.java")
        priorities = [i.priority for i in result.issues]
        assert priorities == sorted(priorities)

    def test_agg002_deduplication(self) -> None:
        """AGG-002: 同一 (category, location, description) の重複除去"""
        dup_issue = make_issue(1, location="Foo#bar", desc="NPE risk")
        outputs = [
            AgentOutput(slot_id="f::m", agent_name="bug_detector", issues=[dup_issue]),
            AgentOutput(slot_id="f::m", agent_name="bug_detector", issues=[dup_issue]),
        ]
        result, _ = aggregate(outputs, "Foo.java")
        assert len(result.issues) == 1

    def test_agg003_no_skips(self) -> None:
        """AGG-003: 全エージェントが正常終了 → skipped_items は空"""
        outputs = [
            AgentOutput(slot_id="f::m", agent_name="bug_detector", issues=[make_issue(1)]),
        ]
        result, skipped = aggregate(outputs, "Foo.java")
        assert len(result.skipped_items) == 0

    def test_agg004_skipped_agents(self) -> None:
        """AGG-004: スキップされたエージェントがある場合"""
        outputs = [
            AgentOutput(
                slot_id="f::m",
                agent_name="bug_detector",
                issues=[make_issue(1)],
            ),
            AgentOutput(
                slot_id="f::m",
                agent_name="security_scanner",
                skipped=True,
                skip_reason="Resource Limit",
            ),
        ]
        result, _ = aggregate(outputs, "Foo.java")
        # スキップされたエージェントのissuesは含まれない
        assert len(result.issues) == 1

    def test_agg005_no_issues(self) -> None:
        """AGG-005: 問題が0件 → 空の issues リスト"""
        outputs = [
            AgentOutput(slot_id="f::m", agent_name="bug_detector", issues=[]),
        ]
        result, _ = aggregate(outputs, "Foo.java")
        assert result.issues == []

    def test_different_issues_not_deduped(self) -> None:
        """異なる問題は重複除去されない"""
        outputs = [
            AgentOutput(
                slot_id="f::m",
                agent_name="bug_detector",
                issues=[
                    make_issue(1, location="Foo#bar", desc="issue A"),
                    make_issue(1, location="Foo#baz", desc="issue B"),
                ],
            ),
        ]
        result, _ = aggregate(outputs, "Foo.java")
        assert len(result.issues) == 2
