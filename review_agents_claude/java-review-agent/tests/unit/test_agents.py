"""AGT-xxx: レビューエージェントテスト（Ollamaモック）"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from java_review_agent.agents.bug_detector import BugDetectorAgent
from java_review_agent.agents.design_critic import DesignCriticAgent
from java_review_agent.agents.efficiency_analyzer import EfficiencyAnalyzerAgent
from java_review_agent.agents.security_scanner import SecurityScannerAgent
from java_review_agent.agents.style_reviewer import StyleReviewerAgent
from java_review_agent.backends.ollama import OllamaBackend
from java_review_agent.schemas.models import CodeSlot


def make_slot(method_name: str = "myMethod") -> CodeSlot:
    return CodeSlot(
        slot_id=f"/path/Foo.java::{method_name}",
        file_path="/path/Foo.java",
        method_name=method_name,
        content='public void myMethod() { String s = null; s.length(); }',
    )


def make_mock_backend(response: str) -> OllamaBackend:
    backend = MagicMock(spec=OllamaBackend)
    backend.generate.return_value = response
    return backend


VALID_JSON_RESPONSE = json.dumps({
    "issues": [
        {
            "priority": 1,
            "category": "bug",
            "severity": "critical",
            "location": "Foo#myMethod",
            "description": "NPE risk",
            "suggestion": "Add null check",
        }
    ]
})


class TestBugDetector:
    def test_agt001_normal_response(self) -> None:
        """AGT-001: Bug Detector 正常なJSONレスポンス"""
        backend = make_mock_backend(VALID_JSON_RESPONSE)
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)

        assert not output.skipped
        assert len(output.issues) == 1
        assert output.issues[0].category == "bug"
        assert len(skipped) == 0

    def test_agt006_invalid_json(self) -> None:
        """AGT-006: LLMが不正なJSON → Skipped (Parse Error)"""
        backend = make_mock_backend("This is not JSON at all!")
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)

        assert output.skipped
        assert output.skip_reason == "Parse Error"
        assert len(skipped) == 1
        assert skipped[0].reason == "Parse Error"

    def test_agt007_oom_error(self) -> None:
        """AGT-007: OOMエラー → Skipped (Resource Limit)"""
        backend = MagicMock(spec=OllamaBackend)
        backend.generate.side_effect = MemoryError("OOM")
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)

        assert output.skipped
        assert output.skip_reason == "Resource Limit"

    def test_agt008_timeout(self) -> None:
        """AGT-008: タイムアウト → Skipped (Resource Limit)"""
        backend = MagicMock(spec=OllamaBackend)
        backend.generate.side_effect = TimeoutError("timeout")
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)

        assert output.skipped
        assert output.skip_reason == "Resource Limit"

    def test_agt009_java_version_in_prompt(self) -> None:
        """AGT-009: {java_version} がプロンプトに埋め込まれる"""
        backend = make_mock_backend(VALID_JSON_RESPONSE)
        agent = BugDetectorAgent(backend)
        prompt = agent.build_prompt(make_slot(), java_version=21)
        assert "21" in prompt

    def test_agt010_retry_success(self) -> None:
        """AGT-010: 1回失敗→2回目成功"""
        backend = MagicMock(spec=OllamaBackend)
        backend.generate.side_effect = [
            Exception("first fail"),
            VALID_JSON_RESPONSE,
        ]
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)

        assert not output.skipped
        assert len(output.issues) == 1

    def test_agt011_all_retries_fail(self) -> None:
        """AGT-011: 2回とも失敗 → Skipped (Resource Limit)"""
        backend = MagicMock(spec=OllamaBackend)
        backend.generate.side_effect = Exception("always fail")
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)

        assert output.skipped
        assert output.skip_reason == "Resource Limit"

    def test_json_in_code_block(self) -> None:
        """```json ... ``` 形式のレスポンスも正しくパース"""
        response = f"```json\n{VALID_JSON_RESPONSE}\n```"
        backend = make_mock_backend(response)
        agent = BugDetectorAgent(backend)
        output, _ = agent.review(make_slot(), java_version=17)
        assert not output.skipped
        assert len(output.issues) == 1

    def test_empty_issues_response(self) -> None:
        """issues が空のJSONレスポンスも正常処理"""
        response = json.dumps({"issues": []})
        backend = make_mock_backend(response)
        agent = BugDetectorAgent(backend)
        output, skipped = agent.review(make_slot(), java_version=17)
        assert not output.skipped
        assert output.issues == []


class TestSecurityScanner:
    def test_agt002_security_normal(self) -> None:
        """AGT-002: Security Scanner 正常なJSONレスポンス"""
        response = json.dumps({
            "issues": [{"priority": 2, "category": "security", "severity": "critical",
                        "location": "Foo#login", "description": "SQL injection", "suggestion": "Use PreparedStatement"}]
        })
        backend = make_mock_backend(response)
        agent = SecurityScannerAgent(backend)
        output, _ = agent.review(make_slot(), java_version=17)
        assert not output.skipped
        assert output.issues[0].category == "security"


class TestEfficiencyAnalyzer:
    def test_agt003_efficiency_normal(self) -> None:
        """AGT-003: Efficiency Analyzer 正常なJSONレスポンス"""
        response = json.dumps({
            "issues": [{"priority": 3, "category": "efficiency", "severity": "minor",
                        "location": "Foo#process", "description": "O(n^2)", "suggestion": "Use HashMap"}]
        })
        backend = make_mock_backend(response)
        agent = EfficiencyAnalyzerAgent(backend)
        output, _ = agent.review(make_slot(), java_version=17)
        assert not output.skipped
        assert output.issues[0].category == "efficiency"


class TestDesignCritic:
    def test_agt004_design_normal(self) -> None:
        """AGT-004: Design Critic 正常なJSONレスポンス"""
        response = json.dumps({
            "issues": [{"priority": 4, "category": "design", "severity": "major",
                        "location": "Foo", "description": "SRP violation", "suggestion": "Split class"}]
        })
        backend = make_mock_backend(response)
        agent = DesignCriticAgent(backend)
        output, _ = agent.review(make_slot(), java_version=17)
        assert not output.skipped
        assert output.issues[0].category == "design"


class TestStyleReviewer:
    def test_agt005_style_normal(self) -> None:
        """AGT-005: Style Reviewer 正常なJSONレスポンス"""
        response = json.dumps({
            "issues": [{"priority": 5, "category": "style", "severity": "minor",
                        "location": "Foo#doStuff", "description": "Poor naming", "suggestion": "Rename"}]
        })
        backend = make_mock_backend(response)
        agent = StyleReviewerAgent(backend)
        output, _ = agent.review(make_slot(), java_version=17)
        assert not output.skipped
        assert output.issues[0].category == "style"
