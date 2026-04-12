"""Retrieverのユニットテスト"""

from unittest.mock import MagicMock, patch

import pytest

from java_qa_agent.retriever import Retriever
from java_qa_agent.schemas.models import SearchResult


class TestRetriever:
    def _make_mock_chroma_result(self, n: int = 3) -> dict:
        """ChromaDB検索結果のモックを生成する"""
        return {
            "ids": [[f"chunk_{i}" for i in range(n)]],
            "documents": [[f"public void method{i}() {{}}" for i in range(n)]],
            "distances": [[0.1 * (i + 1) for i in range(n)]],
            "metadatas": [
                [
                    {
                        "file_path": f"/path/to/File{i}.java",
                        "class_name": f"File{i}",
                        "method_name": f"method{i}",
                        "imports": "[]",
                        "class_signature": f"public class File{i}",
                        "member_vars": "[]",
                        "chunk_type": "method",
                    }
                    for i in range(n)
                ]
            ],
        }

    def test_retriever_returns_top_k_results(self) -> None:
        """top_k件の結果を返すことを確認する"""
        mock_collection = MagicMock()
        mock_collection.query.return_value = self._make_mock_chroma_result(3)
        mock_collection.count.return_value = 5

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch("chromadb.PersistentClient", return_value=mock_client):
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir="/tmp/.indexes",
            )
            results = retriever.retrieve("test-project", "addメソッドを教えてください", top_k=3)

        assert len(results) == 3
        assert all(isinstance(r, SearchResult) for r in results)

    def test_retriever_results_include_score(self) -> None:
        """結果にスコアが含まれることを確認する"""
        mock_collection = MagicMock()
        mock_collection.query.return_value = self._make_mock_chroma_result(2)
        mock_collection.count.return_value = 5

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch("chromadb.PersistentClient", return_value=mock_client):
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir="/tmp/.indexes",
            )
            results = retriever.retrieve("test-project", "質問", top_k=2)

        for result in results:
            assert hasattr(result, "score")
            assert isinstance(result.score, float)

    def test_retriever_empty_index_returns_empty(self) -> None:
        """空のインデックスで空リストを返すことを確認する"""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 0
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "distances": [[]],
            "metadatas": [[]],
        }

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch("chromadb.PersistentClient", return_value=mock_client):
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir="/tmp/.indexes",
            )
            results = retriever.retrieve("test-project", "質問", top_k=5)

        assert results == []

    def test_retriever_index_not_found_raises_error(self) -> None:
        """インデックス未構築でIndexNotFoundErrorを発生させることを確認する"""
        mock_client = MagicMock()
        mock_client.get_collection.side_effect = Exception("Collection not found")

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch("chromadb.PersistentClient", return_value=mock_client):
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir="/tmp/.indexes",
            )
            from java_qa_agent.retriever import IndexNotFoundError

            with pytest.raises(IndexNotFoundError):
                retriever.retrieve("unknown-project", "質問", top_k=5)

    def test_retriever_calls_embed_query(self) -> None:
        """クエリエンベディングが呼ばれることを確認する"""
        mock_collection = MagicMock()
        mock_collection.query.return_value = self._make_mock_chroma_result(1)
        mock_collection.count.return_value = 3

        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_embedder = MagicMock()
        mock_embedder.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch("chromadb.PersistentClient", return_value=mock_client):
            retriever = Retriever(
                embedder=mock_embedder,
                index_base_dir="/tmp/.indexes",
            )
            retriever.retrieve("test-project", "質問", top_k=1)

        mock_embedder.embed_query.assert_called_once_with("質問")
