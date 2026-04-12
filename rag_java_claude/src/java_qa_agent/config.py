"""設定管理モジュール

config.yamlを読み込み、環境変数でマージし、シングルトンとして提供する。
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from java_qa_agent.schemas.models import AppConfig

# .envファイルを読み込む
load_dotenv()

# シングルトンインスタンス
_config_instance: AppConfig | None = None

# デフォルトのconfig.yamlパス（プロジェクトルートに配置）
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config.yaml"


def load_config(config_path: str | None = None) -> AppConfig:
    """指定パスのconfig.yamlを読み込む

    Args:
        config_path: config.yamlのパス。Noneの場合はデフォルトパスを使用する。
                     ファイルが存在しない場合はデフォルト値を使用する。

    Returns:
        AppConfigインスタンス
    """
    config_data: dict = {}

    # config.yamlを読み込む
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if path.exists():
        with open(path) as f:
            loaded = yaml.safe_load(f)
            if loaded:
                config_data = loaded

    # AppConfigを構築（Pydanticがデフォルト値を補完する）
    config = AppConfig(**config_data)

    # 環境変数で上書き
    _apply_env_overrides(config)

    return config


def _apply_env_overrides(config: AppConfig) -> None:
    """環境変数でconfigの値を上書きする

    Args:
        config: 上書き対象のAppConfigインスタンス
    """
    ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
    if ollama_base_url:
        config.ollama.base_url = ollama_base_url


def get_config() -> AppConfig:
    """シングルトンのAppConfigインスタンスを返す

    Returns:
        AppConfigインスタンス（シングルトン）
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def reset_config() -> None:
    """シングルトンをリセットする（テスト用）"""
    global _config_instance
    _config_instance = None
