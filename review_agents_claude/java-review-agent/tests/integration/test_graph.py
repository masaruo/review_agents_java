"""GRP-xxx: LangGraph遷移テスト"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from java_review_agent.config import load_config
from java_review_agent.graph import build_graph
from java_review_agent.state import initial_state


VALID_JSON = json.dumps({"issues": []})


def _make_mock_response() -> MagicMock:
    mock_response = MagicMock()
    mock_response.response = VALID_JSON
    return mock_response


class TestGraphTransitions:
    def test_grp001_normal_flow(self, tmp_path: Path) -> None:
        """GRP-001: .java ファイルあり → 正常フロー（ファイルレポートが生成される）"""
        # プロジェクト構造を作成
        src = tmp_path / "src"
        src.mkdir()
        (src / "Simple.java").write_text("public class Simple { public void m() {} }")

        config = load_config()
        config = config.model_copy(
            update={"output": config.output.model_copy(update={"dir": str(tmp_path / "output")})}
        )

        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.generate.return_value = _make_mock_response()
            mock_client.list.return_value = {"models": []}
            mock_cls.return_value = mock_client

            app = build_graph(config)
            state = initial_state(str(tmp_path), config)
            result = app.invoke(state)

        assert len(result["file_reports"]) == 1
        assert result["summary_content"] is not None

    def test_grp002_no_java_files(self, tmp_path: Path) -> None:
        """GRP-002: .java ファイルなし → file_reports が空"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "readme.txt").write_text("no java")

        config = load_config()
        config = config.model_copy(
            update={"output": config.output.model_copy(update={"dir": str(tmp_path / "output")})}
        )

        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.list.return_value = {"models": []}
            mock_cls.return_value = mock_client

            app = build_graph(config)
            state = initial_state(str(tmp_path), config)
            result = app.invoke(state)

        assert result["file_reports"] == []

    def test_grp003_multiple_files(self, tmp_path: Path) -> None:
        """GRP-003: 複数ファイル処理 → 全ファイル処理後にSummaryが生成される"""
        src = tmp_path / "src"
        src.mkdir()
        (src / "A.java").write_text("public class A { public void m() {} }")
        (src / "B.java").write_text("public class B { public void m() {} }")
        (src / "C.java").write_text("public class C { public void m() {} }")

        config = load_config()
        config = config.model_copy(
            update={"output": config.output.model_copy(update={"dir": str(tmp_path / "output")})}
        )

        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_cls:
            mock_client = MagicMock()
            mock_client.generate.return_value = _make_mock_response()
            mock_client.list.return_value = {"models": []}
            mock_cls.return_value = mock_client

            app = build_graph(config)
            state = initial_state(str(tmp_path), config)
            result = app.invoke(state)

        assert len(result["file_reports"]) == 3
        assert result["summary_content"] is not None
