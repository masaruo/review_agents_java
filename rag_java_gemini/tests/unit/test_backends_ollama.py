from unittest.mock import MagicMock, patch

import pytest

from java_qa_agent.backends.ollama_embed import OllamaEmbed
from java_qa_agent.backends.ollama_llm import OllamaLLM
from java_qa_agent.schemas.models import OllamaConfig


@pytest.fixture
def ollama_config():
    return OllamaConfig(
        base_url="http://mock:11434", model="test-llm", embed_model="test-embed"
    )


@patch("java_qa_agent.backends.ollama_llm.Client")
def test_ollama_llm_generate(mock_client_class, ollama_config):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.generate.return_value = {"response": "Hello world"}

    llm = OllamaLLM(ollama_config)
    response = llm.generate("Hi")

    assert response == "Hello world"
    mock_client.generate.assert_called_once_with(model="test-llm", prompt="Hi")


@patch("java_qa_agent.backends.ollama_embed.Client")
def test_ollama_embed_embed(mock_client_class, ollama_config):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.embeddings.side_effect = [
        {"embedding": [0.1, 0.2]},
        {"embedding": [0.3, 0.4]},
    ]

    embedder = OllamaEmbed(ollama_config)
    embeddings = embedder.embed_batch(["text1", "text2"])

    assert len(embeddings) == 2
    assert embeddings[0] == [0.1, 0.2]
    assert embeddings[1] == [0.3, 0.4]


@patch("java_qa_agent.backends.ollama_llm.Client")
def test_ollama_check_connection(mock_client_class, ollama_config):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.list.return_value = {
        "models": [{"name": "test-llm"}, {"name": "test-embed"}]
    }

    llm = OllamaLLM(ollama_config)
    assert llm.check_connection() is True

    mock_client.list.return_value = {"models": []}
    assert llm.check_connection() is False
