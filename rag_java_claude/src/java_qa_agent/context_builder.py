"""ContextBuilderモジュール

取得チャンク・会話履歴・質問文を結合し、トークン上限内に収まるよう制御する。
"""

import tiktoken

from java_qa_agent.schemas.models import ChatHistory, SearchResult

# システムプロンプトテンプレート
SYSTEM_PROMPT_TEMPLATE = """あなたはJava {java_version}のエキスパートエンジニアです。
提供されたJavaソースコードのコンテキストをもとに、ユーザーの質問に正確かつ詳細に回答してください。

## 回答のガイドライン
- コードに関する説明はMarkdown形式で記述してください
- コードスニペットを示す場合は ```java コードブロック ``` を使用してください
- 不明な点や確認が必要な場合は、正直にその旨を伝えてください
- コンテキストに含まれていない情報について推測する場合は、その旨を明示してください
- バグや問題点を発見した場合は、具体的な修正方法を提示してください"""

# ユーザーメッセージテンプレート
USER_MESSAGE_TEMPLATE = """## コードコンテキスト

{context}

## 会話履歴

{history}

## 質問

{question}"""


class ContextBuilder:
    """コンテキストを構築するクラス

    チャンク・履歴・質問文を結合し、トークン上限を制御する。
    """

    def __init__(
        self,
        java_version: int = 17,
        max_input_tokens: int = 3000,
    ) -> None:
        """初期化

        Args:
            java_version: JavaバージョンをLLMプロンプトに埋め込む
            max_input_tokens: LLMへの最大入力トークン数
        """
        self.java_version = java_version
        self.max_input_tokens = max_input_tokens
        self._encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """テキストのトークン数を計算する

        Args:
            text: 計算対象のテキスト

        Returns:
            トークン数
        """
        return len(self._encoding.encode(text))

    def _format_chunks(self, chunks: list[SearchResult]) -> str:
        """チャンクをフォーマットする

        Args:
            chunks: SearchResultのリスト

        Returns:
            フォーマットされたコンテキスト文字列
        """
        if not chunks:
            return "（関連するコードが見つかりませんでした）"

        parts: list[str] = []
        for result in chunks:
            chunk = result.chunk
            meta = chunk.metadata

            lines = [f"### ファイル: {meta.file_path}"]
            lines.append(f"**クラス**: {meta.class_name}")

            if meta.method_name:
                lines.append(f"**メソッド**: {meta.method_name}")

            if meta.imports:
                lines.append("\n**インポート**:")
                for imp in meta.imports:
                    lines.append(f"  {imp}")

            if meta.class_signature:
                lines.append(f"\n**クラスシグネチャ**: `{meta.class_signature}`")

            if meta.member_vars:
                lines.append("\n**メンバー変数**:")
                for var in meta.member_vars:
                    lines.append(f"  {var}")

            lines.append("\n**コード**:")
            lines.append("```java")
            lines.append(chunk.content)
            lines.append("```")
            lines.append("---")

            parts.append("\n".join(lines))

        return "\n\n".join(parts)

    def _format_history(self, history: ChatHistory) -> str:
        """会話履歴をフォーマットする

        Args:
            history: ChatHistoryオブジェクト

        Returns:
            フォーマットされた履歴文字列
        """
        if not history.turns:
            return "（会話履歴なし）"

        parts: list[str] = []
        for turn in history.turns:
            if turn.role == "user":
                parts.append(f"**ユーザー**: {turn.content}")
            else:
                parts.append(f"**アシスタント**: {turn.content}")
        return "\n\n".join(parts)

    def build(
        self,
        chunks: list[SearchResult],
        history: ChatHistory,
        question: str,
    ) -> str:
        """LLMへの入力プロンプトを構築する

        トークン上限を超える場合は古い履歴から削除する。

        Args:
            chunks: Retrieverが返した検索結果
            history: 会話履歴
            question: ユーザーの質問文

        Returns:
            LLMへの入力プロンプト文字列
        """
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(java_version=self.java_version)
        context_str = self._format_chunks(chunks)

        # 履歴のコピーを作成して切り詰め操作を行う
        working_history = ChatHistory(turns=list(history.turns))

        while True:
            history_str = self._format_history(working_history)
            user_message = USER_MESSAGE_TEMPLATE.format(
                context=context_str,
                history=history_str,
                question=question,
            )
            full_prompt = f"{system_prompt}\n\n{user_message}"
            token_count = self.count_tokens(full_prompt)

            if token_count <= self.max_input_tokens or not working_history.turns:
                return full_prompt

            # 最古のターンを削除する（2ターン分 = ユーザー + アシスタント）
            if len(working_history.turns) >= 2:
                working_history.turns = working_history.turns[2:]
            else:
                working_history.turns = []
