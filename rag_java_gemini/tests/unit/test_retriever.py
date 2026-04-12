from unittest.mock import MagicMock, patch

import pytest

from java_qa_agent.retriever import Retriever
from java_qa_agent.schemas.models import JavaChunk, JavaChunkMetadata


@pytest.fixture
def mock_collection():
    collection = MagicMock()
    return collection


@patch("java_qa_agent.retriever.chromadb.PersistentClient")
def test_retriever_add_chunks(mock_client_class, mock_collection):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.get_or_create_collection.return_value = mock_collection

    retriever = Retriever(index_dir="/tmp/idx", project_name="test")

    chunk = JavaChunk(
        content="code",
        metadata=JavaChunkMetadata(file_path="Main.java", imports="import x;"),
    )

    retriever.add_chunks([chunk], embeddings=[[0.1, 0.2]])

    mock_collection.add.assert_called_once()
    args, kwargs = mock_collection.add.call_args
    assert kwargs["documents"] == ["code"]
    assert kwargs["embeddings"] == [[0.1, 0.2]]
    assert kwargs["metadatas"][0]["file_path"] == "Main.java"


@patch("java_qa_agent.retriever.chromadb.PersistentClient")
def test_retriever_query(mock_client_class, mock_collection):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.get_or_create_collection.return_value = mock_collection

    mock_collection.query.return_value = {
        "documents": [["code1", "code2"]],
        "metadatas": [[{"file_path": "F1"}, {"file_path": "F2"}]],
        "distances": [[0.1, 0.2]],
    }

    retriever = Retriever(index_dir="/tmp/idx", project_name="test")
    results = retriever.query(embedding=[0.1], top_k=2)

    assert len(results) == 2
    assert results[0].content == "code1"
    assert results[0].metadata.file_path == "F1"
