import pytest
from pydantic import ValidationError
from src.java_review_agent.schemas.models import ReviewItem, AppConfig

def test_review_item_valid():
    item = ReviewItem(
        category="BUG",
        priority=1,
        location="Line 10",
        description="NPE risk",
        suggestion="Add null check"
    )
    assert item.category == "BUG"
    assert item.priority == 1

def test_review_item_invalid_priority():
    with pytest.raises(ValidationError):
        ReviewItem(
            category="BUG",
            priority=6, # 1-5 の範囲外
            location="Line 10",
            description="NPE risk",
            suggestion="Add null check"
        )

def test_app_config_validation():
    config_dict = {
        "java_version": 17,
        "ollama": {
            "base_url": "http://localhost:11434",
            "model": "qwen2.5-coder:7b",
            "timeout_seconds": 120
        },
        "processing": {
            "max_concurrency": 1,
            "chunk_token_threshold": 1000,
            "max_input_tokens": 3000,
            "response_reserve_tokens": 1000
        },
        "output_dir": "./review_output"
    }
    config = AppConfig(**config_dict)
    assert config.java_version == 17
    assert config.ollama.model == "qwen2.5-coder:7b"
