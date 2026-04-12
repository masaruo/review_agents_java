from typing import List

from .schemas.models import ChatMessage, JavaChunk


class ContextBuilder:
    def __init__(self, java_version: int, max_tokens: int = 3000):
        self.java_version = java_version
        self.max_tokens = max_tokens

    def build_prompt(
        self, chunks: List[JavaChunk], history: List[ChatMessage], question: str
    ) -> str:
        system_prompt = self._get_system_prompt()

        # Build context from chunks
        context_parts = []
        for chunk in chunks:
            part = f"File: {chunk.metadata.file_path}\n"
            if chunk.metadata.class_signature:
                part += f"Class: {chunk.metadata.class_signature}\n"
            part += f"Code:\n{chunk.content}\n"
            context_parts.append(part)

        context_str = "\n---\n".join(context_parts)

        # Build history string
        history_parts = []
        for msg in history:
            history_parts.append(f"{msg.role}: {msg.content}")
        history_str = "\n".join(history_parts)

        prompt = f"""{system_prompt}

以下のコードコンテキストを参考にしてください：
---
{context_str}
---

会話履歴：
{history_str}

ユーザーの質問：
{question}
"""
        # Simple truncation if too long
        # In a real app, we'd use a tokenizer
        if len(prompt.split()) > self.max_tokens:
            # Simple truncation: take first max_tokens words
            prompt = " ".join(prompt.split()[: self.max_tokens])

        return prompt

    def _get_system_prompt(self) -> str:
        return f"""あなたは Java 専門の高度な AI アシスタントです。
提供されたコードコンテキストと会話履歴に基づいて、ユーザーの質問に正確に回答してください。

### Java 環境
- Java Version: {self.java_version}

### 回答のガイドライン
1. 提供されたコードコンテキストを優先して参照すること。
2. コードが提示されている場合は、そのコードを基に具体的な解決策を提案すること。
3. バグの指摘、リファクタリング、設計のアドバイス、または一般的な Java の質問に対して、プロフェッショナルな回答をすること。
4. 回答は Markdown 形式で行い、コードブロックには言語指定（java, shell 等）を付与すること。
5. コンテキストだけでは回答できない場合は、正直にその旨を伝えること。"""
