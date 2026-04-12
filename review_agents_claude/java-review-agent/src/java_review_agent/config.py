"""config.yaml の読み込みと Config モデルへのマッピング"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from java_review_agent.schemas.models import Config


def load_config(config_path: str | Path = "config.yaml") -> Config:
    """
    config.yaml を読み込み Config モデルを返す。
    ファイルが存在しない場合はデフォルト値で Config を生成する。

    Args:
        config_path: config.yaml のパス（絶対・相対どちらも可）

    Returns:
        Config: 設定モデル
    """
    path = Path(config_path)
    if not path.exists():
        print(f"[WARNING] config file not found: {path}. Using defaults.", file=sys.stderr)
        return Config()

    with path.open("r", encoding="utf-8") as f:
        data: dict = yaml.safe_load(f) or {}

    return Config.model_validate(data)
