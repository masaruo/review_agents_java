from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ReviewItem(BaseModel):
    category: str  # BUG, SECURITY, EFFICIENCY, DESIGN, STYLE
    priority: int = Field(ge=1, le=5)
    location: str
    description: str
    suggestion: str

class ReviewResult(BaseModel):
    agent_name: str
    items: List[ReviewItem]
    status: str = "success"  # success, skipped (resource limit), skipped (parse error)

class SlotReviewData(BaseModel):
    slot_id: str
    results: List[ReviewResult]

class FileReviewData(BaseModel):
    file_path: str
    slots: List[SlotReviewData]
    aggregated_items: List[ReviewItem] = []

class OllamaConfig(BaseModel):
    base_url: str
    model: str
    timeout_seconds: int

class ProcessingConfig(BaseModel):
    max_concurrency: int
    chunk_token_threshold: int
    max_input_tokens: int
    response_reserve_tokens: int

class AppConfig(BaseModel):
    java_version: int
    ollama: OllamaConfig
    processing: ProcessingConfig
    output_dir: str

class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
