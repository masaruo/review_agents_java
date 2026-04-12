"""BaseReviewAgent — 各レビューエージェントの抽象基底クラス"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from java_review_agent.backends.ollama import OllamaBackend
from java_review_agent.schemas.models import AgentOutput, CodeSlot, LLMReviewResponse, SkippedItem


class BaseReviewAgent(ABC):
    """
    全レビューエージェントの抽象基底クラス。
    サブクラスは `agent_name` と `build_prompt` を実装する。
    """

    agent_name: str = "base"
    max_retries: int = 2

    def __init__(self, backend: OllamaBackend) -> None:
        self.backend = backend

    @abstractmethod
    def build_prompt(self, slot: CodeSlot, java_version: int) -> str:
        """プロンプトを生成する"""
        ...

    def _parse_response(self, response_text: str) -> Optional[LLMReviewResponse]:
        """
        LLM の応答テキストから JSON を抽出してパースする。
        パース失敗時は None を返す。
        """
        # JSONブロックを抽出（```json ... ``` または裸の { ... }）
        json_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 最初の { から最後の } までを試みる
            start = response_text.find("{")
            end = response_text.rfind("}")
            if start == -1 or end == -1:
                return None
            json_str = response_text[start : end + 1]

        try:
            data = json.loads(json_str)
            return LLMReviewResponse.model_validate(data)
        except Exception:
            return None

    def review(self, slot: CodeSlot, java_version: int) -> tuple[AgentOutput, list[SkippedItem]]:
        """
        スロットをレビューし、AgentOutput と SkippedItem リストを返す。

        リトライ：最大 max_retries 回試行し、全て失敗した場合はスキップとする。
        """
        prompt = self.build_prompt(slot, java_version)
        last_exc: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response_text = self.backend.generate(prompt)
                parsed = self._parse_response(response_text)

                if parsed is None:
                    return AgentOutput(
                        slot_id=slot.slot_id,
                        agent_name=self.agent_name,
                        skipped=True,
                        skip_reason="Parse Error",
                    ), [
                        SkippedItem(
                            target=slot.slot_id,
                            agent_name=self.agent_name,
                            reason="Parse Error",
                            detail=f"Failed to parse LLM response (attempt {attempt + 1})",
                            timestamp=datetime.now(timezone.utc),
                        )
                    ]

                return AgentOutput(
                    slot_id=slot.slot_id,
                    agent_name=self.agent_name,
                    issues=parsed.issues,
                ), []

            except Exception as exc:
                last_exc = exc
                # OOM / Timeout → リトライ
                continue

        # 全リトライ失敗
        return AgentOutput(
            slot_id=slot.slot_id,
            agent_name=self.agent_name,
            skipped=True,
            skip_reason="Resource Limit",
        ), [
            SkippedItem(
                target=slot.slot_id,
                agent_name=self.agent_name,
                reason="Resource Limit",
                detail=str(last_exc) if last_exc else "Unknown error after retries",
                timestamp=datetime.now(timezone.utc),
            )
        ]
