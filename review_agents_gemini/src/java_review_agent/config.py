import yaml
from src.java_review_agent.schemas.models import AppConfig, OllamaConfig, ProcessingConfig

def load_config(config_path: str = "config.yaml") -> AppConfig:
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    
    return AppConfig(
        java_version=data["java_version"],
        ollama=OllamaConfig(**data["ollama"]),
        processing=ProcessingConfig(**data["processing"]),
        output_dir=data["output"]["dir"]
    )
