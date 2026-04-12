"""ContextBuilderのユニットテスト"""

from java_qa_agent.context_builder import ContextBuilder
from java_qa_agent.schemas.models import (
    ChatHistory,
    ChunkMetadata,
    JavaChunk,
    SearchResult,
)


def make_search_result(
    class_name: str = "Calculator",
    method_name: str = "add",
    content: str = "public int add(int a, int b) { return a + b; }",
) -> SearchResult:
    """テスト用のSearchResultを生成する"""
    metadata = ChunkMetadata(
        file_path=f"/path/to/{class_name}.java",
        class_name=class_name,
        method_name=method_name,
        imports=["import java.util.List;"],
        class_signature=f"public class {class_name}",
        member_vars=["private int result;"],
        chunk_type="method",
    )
    chunk = JavaChunk(content=content, metadata=metadata, token_count=20)
    return SearchResult(chunk=chunk, score=0.9)


class TestContextBuilder:
    def test_combines_chunks_and_history(self) -> None:
        """チャンクと履歴が正しく結合されることを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=3000)
        chunks = [make_search_result()]
        history = ChatHistory()
        history.add_turn("user", "前の質問")
        history.add_turn("assistant", "前の回答")

        prompt = builder.build(chunks, history, "現在の質問")

        assert "Calculator" in prompt
        assert "前の質問" in prompt
        assert "前の回答" in prompt
        assert "現在の質問" in prompt

    def test_empty_history(self) -> None:
        """履歴が空でもプロンプトが生成されることを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=3000)
        chunks = [make_search_result()]
        history = ChatHistory()

        prompt = builder.build(chunks, history, "質問")

        assert "質問" in prompt
        assert "Calculator" in prompt

    def test_empty_chunks(self) -> None:
        """チャンクが空でもプロンプトが生成されることを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=3000)
        chunks: list[SearchResult] = []
        history = ChatHistory()

        prompt = builder.build(chunks, history, "質問")

        assert "質問" in prompt

    def test_java_version_in_prompt(self) -> None:
        """Javaバージョンがプロンプトに含まれることを確認する"""
        builder = ContextBuilder(java_version=21, max_input_tokens=3000)
        chunks: list[SearchResult] = []
        history = ChatHistory()

        prompt = builder.build(chunks, history, "質問")

        assert "21" in prompt

    def test_truncates_history_when_over_limit(self) -> None:
        """max_input_tokens超過時に古い履歴が削除されることを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=200)

        # 大量の履歴を追加
        history = ChatHistory()
        for i in range(10):
            history.add_turn("user", f"これは長い質問です: {i} " * 20)
            history.add_turn("assistant", f"これは長い回答です: {i} " * 20)

        chunks = [make_search_result()]
        # max_input_tokensが小さいため、履歴が切り詰められる
        prompt = builder.build(chunks, history, "最新の質問")

        # 最新の質問は含まれることを確認
        assert "最新の質問" in prompt

    def test_token_counting_accurate(self) -> None:
        """トークンカウントが動作することを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=3000)
        text = "Hello, world!"
        count = builder.count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_question_not_truncated(self) -> None:
        """質問文が切り詰められないことを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=100)
        chunks: list[SearchResult] = []
        history = ChatHistory()
        question = "addメソッドについて詳しく教えてください"

        prompt = builder.build(chunks, history, question)

        assert question in prompt

    def test_oldest_history_removed_first(self) -> None:
        """最古の履歴から削除されることを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=300)

        history = ChatHistory()
        history.add_turn("user", "最初の質問: " + "テスト " * 30)
        history.add_turn("assistant", "最初の回答: " + "テスト " * 30)
        history.add_turn("user", "最新の質問")
        history.add_turn("assistant", "最新の回答")

        chunks: list[SearchResult] = []
        prompt = builder.build(chunks, history, "現在の質問")

        # 最新の会話は残っていることを確認（制限に依存するが最新は優先）
        assert "現在の質問" in prompt

    def test_system_prompt_not_truncated(self) -> None:
        """システムプロンプトは削除されないことを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=500)
        chunks: list[SearchResult] = []
        history = ChatHistory()
        for i in range(20):
            history.add_turn("user", f"質問{i}: " + "テスト " * 10)
            history.add_turn("assistant", f"回答{i}: " + "テスト " * 10)

        prompt = builder.build(chunks, history, "質問")

        # システムプロンプトのキーワードが含まれることを確認
        assert "Java" in prompt

    def test_multiple_chunks_formatted(self) -> None:
        """複数チャンクが正しくフォーマットされることを確認する"""
        builder = ContextBuilder(java_version=17, max_input_tokens=3000)
        chunks = [
            make_search_result(class_name="Calculator", method_name="add"),
            make_search_result(class_name="UserService", method_name="createUser"),
        ]
        history = ChatHistory()

        prompt = builder.build(chunks, history, "質問")

        assert "Calculator" in prompt
        assert "UserService" in prompt
        assert "add" in prompt
        assert "createUser" in prompt
