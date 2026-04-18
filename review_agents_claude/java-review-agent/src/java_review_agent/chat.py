"""追加質問ハンドラ — レビュー結果をコンテキストにOllamaへ問い合わせる"""

from __future__ import annotations

from typing import Generator

import ollama


class ChatHandler:
    """
    レビュー結果をコンテキストとして保持し、
    追加質問に対してストリーミング回答を生成する。
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        review_context: str,
    ) -> None:
        self._client = ollama.Client(host=base_url)
        self._model = model
        self._system_prompt = (
            "あなたはJavaコードレビューの専門家です。"
            "以下のコードレビュー結果を参照して、ユーザーの質問に日本語で回答してください。\n\n"
            "## レビュー結果\n\n"
            f"{review_context}"
        )

    def stream(
        self,
        message: str,
        history: list[dict[str, str]],
    ) -> Generator[str, None, None]:
        """
        会話履歴と新しいメッセージをもとにストリーミング回答を生成する。

        Args:
            message: ユーザーの新しい質問
            history: これまでの会話履歴（{"role": "user"|"assistant", "content": str} のリスト）

        Yields:
            回答のデルタ文字列
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt},
            *history,
            {"role": "user", "content": message},
        ]

        stream = self._client.chat(
            model=self._model,
            messages=messages,  # type: ignore[arg-type]
            stream=True,
        )
        for chunk in stream:
            delta: str = chunk.message.content or ""
            if delta:
                yield delta
