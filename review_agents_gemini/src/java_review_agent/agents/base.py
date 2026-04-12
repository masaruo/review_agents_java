from abc import ABC, abstractmethod
from typing import List, Dict, Any
from src.java_review_agent.schemas.models import ReviewResult, ReviewItem
from src.java_review_agent.backends.ollama import OllamaBackend

class BaseReviewAgent(ABC):
    def __init__(self, backend: OllamaBackend, model: str, java_version: int):
        self.backend = backend
        self.model = model
        self.java_version = java_version

    @abstractmethod
    def get_prompt(self, code: str, context: str) -> str:
        pass

    @property
    @abstractmethod
    def agent_name(self) -> str:
        pass

    def review(self, code: str, context: str) -> ReviewResult:
        prompt = self.get_prompt(code, context)
        try:
            response = self.backend.generate_json(self.model, prompt)
            items = [ReviewItem(**item) for item in response.get("items", [])]
            return ReviewResult(
                agent_name=self.agent_name,
                items=items,
                status="success"
            )
        except Exception as e:
            # TODO: ログ出力
            return ReviewResult(
                agent_name=self.agent_name,
                items=[],
                status=f"skipped (error: {str(e)})"
            )
