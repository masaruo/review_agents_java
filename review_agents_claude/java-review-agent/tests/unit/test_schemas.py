"""SCH-xxx: Pydanticモデルバリデーションテスト"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from java_review_agent.schemas.models import (
    CodeSlot,
    Config,
    DEFAULT_AGENTS,
    OllamaConfig,
    ProcessingConfig,
    ReviewInstruction,
    ReviewIssue,
    SkippedItem,
)


class TestReviewIssue:
    def test_sch001_normal_creation(self) -> None:
        """SCH-001: ReviewIssue の正常生成"""
        issue = ReviewIssue(
            priority=1,
            category="bug",
            severity="critical",
            location="Foo#bar",
            description="NPE risk",
            suggestion="Add null check",
        )
        assert issue.priority == 1
        assert issue.category == "bug"
        assert issue.severity == "critical"

    def test_sch002_priority_zero_invalid(self) -> None:
        """SCH-002: priority=0 は無効"""
        with pytest.raises(ValidationError):
            ReviewIssue(
                priority=0,
                category="bug",
                severity="critical",
                location="Foo#bar",
                description="d",
                suggestion="s",
            )

    def test_sch003_priority_six_invalid(self) -> None:
        """SCH-003: priority=6 は無効"""
        with pytest.raises(ValidationError):
            ReviewIssue(
                priority=6,
                category="bug",
                severity="critical",
                location="Foo#bar",
                description="d",
                suggestion="s",
            )

    def test_sch004_invalid_severity(self) -> None:
        """SCH-004: severity='unknown' は無効"""
        with pytest.raises(ValidationError):
            ReviewIssue(
                priority=1,
                category="bug",
                severity="unknown",  # type: ignore[arg-type]
                location="Foo#bar",
                description="d",
                suggestion="s",
            )

    def test_sch005_invalid_category(self) -> None:
        """SCH-005: category='unknown' は無効"""
        with pytest.raises(ValidationError):
            ReviewIssue(
                priority=1,
                category="unknown",  # type: ignore[arg-type]
                severity="critical",
                location="Foo#bar",
                description="d",
                suggestion="s",
            )

    def test_all_valid_priorities(self) -> None:
        """priority 1〜5 は全て有効"""
        for p in range(1, 6):
            issue = ReviewIssue(
                priority=p,
                category="bug",
                severity="info",
                location="Foo",
                description="d",
                suggestion="s",
            )
            assert issue.priority == p

    def test_all_valid_severities(self) -> None:
        """全severity値が有効"""
        for sev in ("critical", "major", "minor", "info"):
            issue = ReviewIssue(
                priority=1,
                category="bug",
                severity=sev,  # type: ignore[arg-type]
                location="Foo",
                description="d",
                suggestion="s",
            )
            assert issue.severity == sev

    def test_all_valid_categories(self) -> None:
        """全category値が有効"""
        for cat in ("bug", "security", "efficiency", "design", "style"):
            issue = ReviewIssue(
                priority=1,
                category=cat,  # type: ignore[arg-type]
                severity="info",
                location="Foo",
                description="d",
                suggestion="s",
            )
            assert issue.category == cat


class TestSkippedItem:
    def test_sch006_invalid_reason(self) -> None:
        """SCH-006: reason が不正な値の場合は ValidationError"""
        with pytest.raises(ValidationError):
            SkippedItem(
                target="Foo.java",
                agent_name="bug_detector",
                reason="Unknown Reason",  # type: ignore[arg-type]
                detail="detail",
            )

    def test_valid_reasons(self) -> None:
        """有効な reason 値"""
        for reason in ("Resource Limit", "Parse Error", "Connection Error"):
            item = SkippedItem(
                target="Foo.java",
                agent_name="bug_detector",
                reason=reason,  # type: ignore[arg-type]
                detail="detail",
            )
            assert item.reason == reason


class TestCodeSlot:
    def test_sch007_normal_creation(self) -> None:
        """SCH-007: CodeSlot の正常生成"""
        slot = CodeSlot(
            slot_id="/path/Foo.java::myMethod",
            file_path="/path/Foo.java",
            method_name="myMethod",
            content="public void myMethod() {}",
        )
        assert slot.slot_id == "/path/Foo.java::myMethod"
        assert slot.is_truncated is False

    def test_whole_slot_id(self) -> None:
        """whole スロットの slot_id 形式"""
        slot = CodeSlot(
            slot_id="/path/Foo.java::whole",
            file_path="/path/Foo.java",
            method_name="whole",
            content="...",
        )
        assert slot.method_name == "whole"
        assert slot.slot_id.endswith("::whole")


class TestReviewInstruction:
    def test_sch009_default_values(self) -> None:
        """SCH-009: ReviewInstruction デフォルト値の確認"""
        instr = ReviewInstruction()
        assert instr.scope == "full"
        assert instr.scope_target is None
        assert instr.focus_question is None
        assert set(instr.enabled_agents) == set(DEFAULT_AGENTS)

    def test_sch010_invalid_scope(self) -> None:
        """SCH-010: scope に不正な値は ValidationError"""
        with pytest.raises(ValidationError):
            ReviewInstruction(scope="all")  # type: ignore[arg-type]

    def test_sch011_invalid_agent_name(self) -> None:
        """SCH-011: enabled_agents に不正なエージェント名は ValidationError"""
        with pytest.raises(ValidationError):
            ReviewInstruction(enabled_agents=["unknown_agent"])  # type: ignore[arg-type]

    def test_sch012_empty_enabled_agents(self) -> None:
        """SCH-012: enabled_agents が空リストでも生成できる"""
        instr = ReviewInstruction(enabled_agents=[])
        assert instr.enabled_agents == []

    def test_valid_scopes(self) -> None:
        """全 scope 値が有効"""
        for scope in ("full", "file", "class", "function"):
            instr = ReviewInstruction(scope=scope)  # type: ignore[arg-type]
            assert instr.scope == scope

    def test_with_all_fields(self) -> None:
        """全フィールド指定で正常生成"""
        instr = ReviewInstruction(
            scope="function",
            scope_target="authenticate",
            enabled_agents=["bug_detector", "security_scanner", "design_critic"],
            focus_question="このメソッドの設計はどう思う？",
        )
        assert instr.scope == "function"
        assert instr.scope_target == "authenticate"
        assert "design_critic" in instr.enabled_agents
        assert instr.focus_question == "このメソッドの設計はどう思う？"


class TestConfig:
    def test_sch008_default_values(self) -> None:
        """SCH-008: Config デフォルト値の確認"""
        cfg = Config()
        assert cfg.java_version == 17
        assert cfg.ollama.base_url == "http://localhost:11434"
        assert cfg.ollama.model == "qwen2.5-coder:7b"
        assert cfg.ollama.timeout_seconds == 120
        assert cfg.processing.max_concurrency == 1
        assert cfg.processing.chunk_token_threshold == 1000
        assert cfg.processing.max_input_tokens == 3000
        assert cfg.processing.response_reserve_tokens == 1000
        assert cfg.output.dir == "./review_output"

    def test_invalid_max_concurrency(self) -> None:
        """max_concurrency=0 は無効"""
        with pytest.raises(ValidationError):
            ProcessingConfig(max_concurrency=0)

    def test_invalid_chunk_threshold(self) -> None:
        """chunk_token_threshold=50 は無効（最小100）"""
        with pytest.raises(ValidationError):
            ProcessingConfig(chunk_token_threshold=50)

    def test_invalid_max_input_tokens(self) -> None:
        """max_input_tokens=100 は無効（最小500）"""
        with pytest.raises(ValidationError):
            ProcessingConfig(max_input_tokens=100)
