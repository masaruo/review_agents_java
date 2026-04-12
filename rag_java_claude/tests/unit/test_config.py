"""設定読み込みのユニットテスト"""

import os
import tempfile

import pytest

from java_qa_agent.config import get_config, load_config, reset_config
from java_qa_agent.schemas.models import AppConfig

SAMPLE_CONFIG_YAML = """
java_version: 17
ollama:
  base_url: "http://localhost:11434"
  model: "qwen2.5-coder:7b"
  embed_model: "nomic-embed-text"
  timeout_seconds: 120
rag:
  top_k: 5
  chunk_token_threshold: 1000
  max_input_tokens: 3000
  max_history_turns: 6
storage:
  index_dir: "~/.java_qa_agent/indexes"
  log_dir: "~/.java_qa_agent/logs"
  save_logs: true
"""


class TestLoadConfig:
    def test_load_from_yaml_string(self) -> None:
        """YAML文字列から設定を読み込めることを確認する"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(SAMPLE_CONFIG_YAML)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.java_version == 17
            assert config.ollama.model == "qwen2.5-coder:7b"
            assert config.rag.top_k == 5
            assert config.storage.save_logs is True
        finally:
            os.unlink(temp_path)

    def test_default_config_when_no_file(self) -> None:
        """ファイルなしでデフォルト値が使われることを確認する"""
        config = load_config(None)
        assert isinstance(config, AppConfig)
        assert config.java_version == 17
        assert config.ollama.base_url == "http://localhost:11434"

    def test_load_nonexistent_file_uses_defaults(self) -> None:
        """存在しないファイルを指定した場合はデフォルト値を使用することを確認する"""
        config = load_config("/nonexistent/path/config.yaml")
        assert isinstance(config, AppConfig)
        assert config.java_version == 17

    def test_partial_yaml_uses_defaults_for_missing(self) -> None:
        """部分的なYAMLの場合、欠落した値にデフォルトが使われることを確認する"""
        partial_yaml = "java_version: 21\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(partial_yaml)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.java_version == 21
            # デフォルト値が使用されること
            assert config.ollama.model == "qwen2.5-coder:7b"
        finally:
            os.unlink(temp_path)


class TestGetConfig:
    def setup_method(self) -> None:
        """各テスト前にシングルトンをリセットする"""
        reset_config()

    def test_config_singleton(self) -> None:
        """get_config()が同じインスタンスを返すことを確認する"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_returns_app_config(self) -> None:
        """get_config()がAppConfigインスタンスを返すことを確認する"""
        config = get_config()
        assert isinstance(config, AppConfig)

    def test_env_override_ollama_base_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数OLLAMA_BASE_URLで上書きできることを確認する"""
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://remote-server:11434")
        reset_config()
        config = get_config()
        assert config.ollama.base_url == "http://remote-server:11434"
