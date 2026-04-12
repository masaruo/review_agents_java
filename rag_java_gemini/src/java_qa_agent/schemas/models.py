from datetime import datetime

from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    embed_model: str = "nomic-embed-text"
    timeout_seconds: int = 120


class RagConfig(BaseModel):
    top_k: int = 5
    chunk_token_threshold: int = 1000
    max_chunk_chars: int = 6000
    max_input_tokens: int = 3000
    max_history_turns: int = 6


class StorageConfig(BaseModel):
    index_dir: str = "~/.java_qa_agent/indexes"
    log_dir: str = "~/.java_qa_agent/logs"
    save_logs: bool = True


class Config(BaseModel):
    java_version: int = 17
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    rag: RagConfig = Field(default_factory=RagConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)


class JavaChunkMetadata(BaseModel):
    file_path: str
    imports: str = ""
    class_signature: str = ""
    member_variables: str = ""
    chunk_type: str = "method"  # "method" or "full_file"


class JavaChunk(BaseModel):
    content: str
    metadata: JavaChunkMetadata


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
