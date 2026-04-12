
import pytest
import yaml

from java_qa_agent.config import load_config


@pytest.fixture
def sample_config_file(tmp_path):
    config_data = {
        "java_version": 11,
        "ollama": {
            "base_url": "http://test:11434",
            "model": "test-model",
            "embed_model": "test-embed",
            "timeout_seconds": 60,
        },
        "rag": {
            "top_k": 3,
            "chunk_token_threshold": 500,
            "max_input_tokens": 1000,
            "max_history_turns": 3,
        },
        "storage": {
            "index_dir": "/tmp/indexes",
            "log_dir": "/tmp/logs",
            "save_logs": False,
        },
    }
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)
    return config_path


def test_load_config(sample_config_file):
    config = load_config(sample_config_file)
    assert config.java_version == 11
    assert config.ollama.model == "test-model"
    assert config.rag.top_k == 3
    assert config.storage.save_logs is False


def test_load_config_default_values(tmp_path):
    # Empty config or minimal config
    config_path = tmp_path / "minimal_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"java_version": 17}, f)

    config = load_config(config_path)
    assert config.java_version == 17
    # Check if defaults are applied
    assert config.ollama.base_url == "http://localhost:11434"
    assert config.rag.top_k == 5
