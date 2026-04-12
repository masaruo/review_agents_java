"""Ollamaバックエンド — 接続確認・推論リクエスト・シリアル実行制御"""

from __future__ import annotations

import asyncio
import sys
from typing import Optional

import ollama


# グローバルセマフォ（シリアル実行制御）
_semaphore: Optional[asyncio.Semaphore] = None


def _get_semaphore(max_concurrency: int = 1) -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(max_concurrency)
    return _semaphore


def reset_semaphore(max_concurrency: int = 1) -> None:
    """テストや再初期化用にセマフォをリセットする"""
    global _semaphore
    _semaphore = asyncio.Semaphore(max_concurrency)


def check_ollama_connection(base_url: str, model: str) -> None:
    """
    Ollama への接続確認を行う。
    失敗した場合は STDERR にエラーを出力して SystemExit する。

    Args:
        base_url: Ollama エンドポイント
        model: 使用モデル名
    """
    try:
        client = ollama.Client(host=base_url)
        # モデル一覧を取得して接続確認
        client.list()
    except Exception as exc:
        print(
            f"[ERROR] Failed to connect to Ollama.\n"
            f"  Error type   : {type(exc).__name__}\n"
            f"  Endpoint     : {base_url}\n"
            f"  Model        : {model}\n"
            f"  Detail       : {exc}\n"
            f"  Recommended  : Please start Ollama with `ollama serve` and ensure "
            f"the model is pulled with `ollama pull {model}`.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


class OllamaBackend:
    """
    Ollama との同期推論インタフェース。
    シリアル実行はグラフ側（ノードを直列に接続）で制御するため、
    このクラスは単純なラッパーとして機能する。
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b",
        timeout_seconds: int = 120,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = ollama.Client(host=base_url)

    def generate(self, prompt: str) -> str:
        """
        Ollama に推論リクエストを送信し、応答テキストを返す。

        Args:
            prompt: 送信するプロンプト

        Returns:
            LLM の応答テキスト

        Raises:
            ollama.ResponseError: OOM等のエラー
            TimeoutError: タイムアウト
        """
        response = self._client.generate(
            model=self.model,
            prompt=prompt,
            options={"num_predict": 1024},
        )
        return response.response
