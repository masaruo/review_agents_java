"""CFG-xxx: 設定管理テスト"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from java_review_agent.config import load_config
from java_review_agent.schemas.models import Config


class TestLoadConfig:
    def test_cfg001_default_config(self) -> None:
        """CFG-001: デフォルト値で Config を生成"""
        cfg = load_config("nonexistent_config.yaml")
        assert cfg.java_version == 17
        assert cfg.processing.max_concurrency == 1

    def test_cfg002_load_from_file(self, tmp_path: Path) -> None:
        """CFG-002: config.yaml から設定を読み込み"""
        config_data = {
            "java_version": 11,
            "ollama": {"base_url": "http://localhost:11434", "model": "qwen2.5-coder:7b", "timeout_seconds": 60},
            "processing": {
                "max_concurrency": 2,
                "chunk_token_threshold": 500,
                "max_input_tokens": 2000,
                "response_reserve_tokens": 500,
            },
            "output": {"dir": "./out"},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        cfg = load_config(str(config_file))
        assert cfg.java_version == 11
        assert cfg.processing.max_concurrency == 2
        assert cfg.processing.chunk_token_threshold == 500
        assert cfg.output.dir == "./out"

    def test_cfg005_missing_config_file_uses_defaults(self) -> None:
        """CFG-005: 存在しない config.yaml → デフォルト値で動作"""
        cfg = load_config("/nonexistent/path/config.yaml")
        assert isinstance(cfg, Config)
        assert cfg.java_version == 17

    def test_partial_config_merges_defaults(self, tmp_path: Path) -> None:
        """一部のみ指定した場合も残りはデフォルト値"""
        config_data = {"java_version": 21}
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        cfg = load_config(str(config_file))
        assert cfg.java_version == 21
        assert cfg.processing.max_concurrency == 1  # default
