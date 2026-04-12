"""OLL-xxx: Ollama通信テスト（モック）"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from java_review_agent.backends.ollama import OllamaBackend, check_ollama_connection


class TestCheckOllamaConnection:
    def test_oll001_success(self) -> None:
        """OLL-001: 接続確認（モック）：成功"""
        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.list.return_value = {"models": []}
            mock_client_cls.return_value = mock_client

            # SystemExitが発生しなければ成功
            check_ollama_connection("http://localhost:11434", "qwen2.5-coder:7b")

    def test_oll002_failure_exits(self) -> None:
        """OLL-002: 接続確認（モック）：失敗 → SystemExit"""
        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.list.side_effect = ConnectionRefusedError("Connection refused")
            mock_client_cls.return_value = mock_client

            with pytest.raises(SystemExit) as exc_info:
                check_ollama_connection("http://localhost:11434", "qwen2.5-coder:7b")
            assert exc_info.value.code == 1

    def test_oll003_generate_success(self) -> None:
        """OLL-003: 推論リクエスト（モック）：正常"""
        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.response = '{"issues": []}'
            mock_client.generate.return_value = mock_response
            mock_client_cls.return_value = mock_client

            backend = OllamaBackend()
            result = backend.generate("test prompt")
            assert result == '{"issues": []}'

    def test_oll004_timeout(self) -> None:
        """OLL-004: 推論リクエスト（モック）：タイムアウト"""
        with patch("java_review_agent.backends.ollama.ollama.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.generate.side_effect = TimeoutError("timeout")
            mock_client_cls.return_value = mock_client

            backend = OllamaBackend()
            with pytest.raises(TimeoutError):
                backend.generate("test prompt")
