import pytest
from unittest.mock import patch, MagicMock
from src.java_review_agent.backends.ollama import OllamaBackend

@patch("ollama.Client")
def test_ollama_backend_check_connection(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_client.list.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}
    
    backend = OllamaBackend(base_url="http://localhost:11434")
    assert backend.check_connection() is True

@patch("ollama.Client")
def test_ollama_backend_check_connection_fail(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_client.list.side_effect = Exception("Connection refused")
    
    backend = OllamaBackend(base_url="http://localhost:11434")
    assert backend.check_connection() is False

@patch("ollama.Client")
def test_ollama_backend_generate_json(mock_client_class):
    mock_client = mock_client_class.return_value
    mock_client.generate.return_value = {"response": '{"items": []}'}
    
    backend = OllamaBackend(base_url="http://localhost:11434")
    response = backend.generate_json("qwen2.5-coder:7b", "prompt")
    assert response == {"items": []}
