from typing import List

from .schemas.models import ChatMessage


class ChatSession:
    def __init__(self, max_history: int = 6):
        self.max_history = max_history
        self.history: List[ChatMessage] = []

    def add_message(self, role: str, content: str) -> None:
        self.history.append(ChatMessage(role=role, content=content))
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def get_history(self) -> List[ChatMessage]:
        return self.history

    def clear_history(self) -> None:
        self.history = []
