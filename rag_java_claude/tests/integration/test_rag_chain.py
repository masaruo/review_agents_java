"""RAGチェーンの統合テスト（モック使用）"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from java_qa_agent.chat_session import ChatSession
from java_qa_agent.context_builder import ContextBuilder
from java_qa_agent.indexer import Indexer
from java_qa_agent.retriever import Retriever
from java_qa_agent.schemas.models import (
    AppConfig,
    ChunkMetadata,
    JavaChunk,
    OllamaConfig,
    RagConfig,
    SearchResult,
    StorageConfig,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "sample_java"


def make_config() -> AppConfig:
    """テスト用設定を生成する"""
    return AppConfig(
        java_version=17,
        ollama=OllamaConfig(
            base_url="http://localhost:11434",
            model="qwen2.5-coder:7b",
            embed_model="nomic-embed-text",
            timeout_seconds=120,
        ),
        rag=RagConfig(
            top_k=3,
            chunk_token_threshold=1000,
            max_input_tokens=3000,
            max_history_turns=3,
        ),
        storage=StorageConfig(
            index_dir="/tmp/.test_indexes",
            log_dir="/tmp/.test_logs",
            save_logs=False,
        ),
    )


def make_mock_search_result(method_name: str = "add") -> SearchResult:
    """テスト用のSearchResultを生成する"""
    metadata = ChunkMetadata(
        file_path="/path/to/Calculator.java",
        class_name="Calculator",
        method_name=method_name,
        imports=["import java.util.List;"],
        class_signature="public class Calculator",
        member_vars=["private int result;"],
        chunk_type="method",
    )
    chunk = JavaChunk(
        content=f"public int {method_name}(int a, int b) {{ return a + b; }}",
        metadata=metadata,
        token_count=20,
    )
    return SearchResult(chunk=chunk, score=0.9)


class TestIndexRetrieveGenerateChain:
    def test_index_retrieve_generate_produces_answer(self, tmp_path: Path) -> None:
        """インデックス→検索→生成の一連のフローが正しく動作することを確認する（全モック）"""
        # モック設定
        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [[0.1, 0.2, 0.3]] * 5
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        mock_collection = MagicMock()
        mock_collection.count.return_value = 2  # インデックスにデータが存在する
        mock_collection.query.return_value = {
            "ids": [["chunk_0", "chunk_1"]],
            "documents": [
                [
                    "public int add(int a, int b) { return a + b; }",
                    "public int subtract(int a, int b) { return a - b; }",
                ]
            ],
            "distances": [[0.1, 0.2]],
            "metadatas": [
                [
                    {
                        "file_path": "/path/to/Calculator.java",
                        "class_name": "Calculator",
                        "method_name": "add",
                        "imports": "[]",
                        "class_signature": "public class Calculator",
                        "member_vars": "[]",
                        "chunk_type": "method",
                    },
                    {
                        "file_path": "/path/to/Calculator.java",
                        "class_name": "Calculator",
                        "method_name": "subtract",
                        "imports": "[]",
                        "class_signature": "public class Calculator",
                        "member_vars": "[]",
                        "chunk_type": "method",
                    },
                ]
            ],
        }

        mock_client = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_client.get_collection.return_value = mock_collection

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "addメソッドは2つの整数を加算して返します。"

        # Indexerでインデックス構築（src/ディレクトリを使用）
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "Calculator.java").write_text((FIXTURES_DIR / "Calculator.java").read_text())

        with patch("chromadb.PersistentClient", return_value=mock_client):
            indexer = Indexer(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            chunk_count = indexer.build_index("test-project", str(tmp_path))
            assert chunk_count > 0

            # Retrieverで検索
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir=str(tmp_path / ".indexes"),
            )
            results = retriever.retrieve("test-project", "addメソッドを教えてください", top_k=3)

        assert len(results) > 0

        # ContextBuilderでプロンプト構築
        from java_qa_agent.schemas.models import ChatHistory

        context_builder = ContextBuilder(
            java_version=17,
            max_input_tokens=3000,
        )
        history = ChatHistory()
        prompt = context_builder.build(results, history, "addメソッドを教えてください")
        assert "addメソッドを教えてください" in prompt

        # LLMで回答生成
        answer = mock_llm.generate(prompt)
        assert "addメソッドは" in answer


class TestMultiTurnConversation:
    def test_second_question_has_context(self) -> None:
        """マルチターンで2問目に1問目の文脈が引き継がれることを確認する"""
        config = make_config()
        mock_llm = MagicMock()
        mock_llm.generate.side_effect = ["最初の回答です", "2番目の回答です"]

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = [make_mock_search_result()]

        mock_logger = MagicMock()

        session = ChatSession(
            project_name="test-project",
            config=config,
            llm=mock_llm,
            retriever=mock_retriever,
            logger=mock_logger,
        )

        # 1問目
        response1 = session.process_turn("addメソッドを教えてください")
        assert response1 == "最初の回答です"

        # 2問目
        response2 = session.process_turn("それはスレッドセーフですか？")
        assert response2 == "2番目の回答です"

        # 2問目のLLM呼び出しのプロンプトに1問目の内容が含まれているか確認
        second_call_prompt = mock_llm.generate.call_args_list[1][0][0]
        assert "addメソッドを教えてください" in second_call_prompt
        assert "最初の回答です" in second_call_prompt

    def test_history_is_included_in_subsequent_prompts(self) -> None:
        """履歴が後続のプロンプトに含まれることを確認する"""
        config = make_config()
        prompts_used: list[str] = []

        def capture_prompt(prompt: str) -> str:
            prompts_used.append(prompt)
            return "回答"

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = capture_prompt

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []

        mock_logger = MagicMock()

        session = ChatSession(
            project_name="test-project",
            config=config,
            llm=mock_llm,
            retriever=mock_retriever,
            logger=mock_logger,
        )

        session.process_turn("最初の質問")
        session.process_turn("2番目の質問")

        # 2番目のプロンプトに1番目の会話が含まれていること
        assert len(prompts_used) == 2
        assert "最初の質問" in prompts_used[1]
