"""エラーハンドリングのユニットテスト"""

from unittest.mock import MagicMock, patch

import pytest

from java_qa_agent.backends.ollama_llm import OllamaLLM
from java_qa_agent.retriever import IndexNotFoundError, Retriever


class TestOllamaConnectionError:
    def test_ollama_connection_failure(self) -> None:
        """Ollama未起動時に適切なエラーが発生することを確認する"""

        with patch("ollama.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list.side_effect = Exception("Connection refused")
            mock_client_class.return_value = mock_client

            llm = OllamaLLM(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

            assert llm.check_connection() is False

    def test_ollama_connection_success(self) -> None:
        """Ollama起動時に接続成功することを確認する"""
        with patch("ollama.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list.return_value = {"models": []}
            mock_client_class.return_value = mock_client

            llm = OllamaLLM(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

            assert llm.check_connection() is True

    def test_model_not_found(self) -> None:
        """モデル未取得時に適切なエラーが発生することを確認する"""
        with patch("ollama.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list.return_value = {"models": [{"name": "llama3:8b"}]}
            mock_client_class.return_value = mock_client

            llm = OllamaLLM(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

            assert llm.check_model_available("qwen2.5-coder:7b") is False

    def test_model_found(self) -> None:
        """モデルが存在する場合にTrueを返すことを確認する"""
        with patch("ollama.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}
            mock_client_class.return_value = mock_client

            llm = OllamaLLM(base_url="http://localhost:11434", model="qwen2.5-coder:7b")

            assert llm.check_model_available("qwen2.5-coder:7b") is True

    def test_embedding_model_not_found(self) -> None:
        """エンベディングモデル未取得時に適切な結果になることを確認する"""
        from java_qa_agent.backends.ollama_embed import OllamaEmbedding

        with patch("ollama.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}
            mock_client_class.return_value = mock_client

            embedder = OllamaEmbedding(
                base_url="http://localhost:11434",
                model="nomic-embed-text",
            )

            assert embedder.check_model_available("nomic-embed-text") is False


class TestIndexNotFoundError:
    def test_index_not_found_error(self) -> None:
        """インデックス未構築でIndexNotFoundErrorが発生することを確認する"""
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Collection not found")

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch("chromadb.PersistentClient", return_value=mock_client):
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir="/tmp/.indexes",
            )

            with pytest.raises(IndexNotFoundError) as exc_info:
                retriever.retrieve("unknown-project", "質問", top_k=5)

            # エラーメッセージにプロジェクト名が含まれることを確認
            assert "unknown-project" in str(exc_info.value)

    def test_index_not_found_error_message(self) -> None:
        """IndexNotFoundErrorのメッセージが適切であることを確認する"""
        error = IndexNotFoundError("test-project")
        assert "test-project" in str(error)


class TestLLMParseError:
    def test_llm_parse_error_is_caught(self) -> None:
        """LLMパースエラーがchatセッションで捕捉されることを確認する"""
        from java_qa_agent.chat_session import ChatSession
        from java_qa_agent.schemas.models import AppConfig, OllamaConfig, RagConfig, StorageConfig

        config = AppConfig(
            java_version=17,
            ollama=OllamaConfig(),
            rag=RagConfig(),
            storage=StorageConfig(save_logs=False),
        )

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = ValueError("LLMパースエラー")
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

        # エラーが発生してもセッションが終了しないこと
        result = session.process_turn("質問")
        # エラー時はNoneまたはエラー文字列を返す
        assert result is None or isinstance(result, str)
