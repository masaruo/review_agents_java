"""Pydantic v2 モデル定義"""

from datetime import datetime

from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    """Ollamaバックエンドの設定"""

    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    embed_model: str = "nomic-embed-text"
    timeout_seconds: int = 120


class RagConfig(BaseModel):
    """RAGパイプラインの設定"""

    top_k: int = 5
    chunk_token_threshold: int = 1000
    max_input_tokens: int = 3000
    max_history_turns: int = 6


class StorageConfig(BaseModel):
    """ストレージ設定"""

    index_dir: str = "~/.java_qa_agent/indexes"
    log_dir: str = "~/.java_qa_agent/logs"
    save_logs: bool = True


class AppConfig(BaseModel):
    """アプリケーション全体の設定"""

    java_version: int = 17
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    rag: RagConfig = Field(default_factory=RagConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)


class ChunkMetadata(BaseModel):
    """Javaチャンクのメタデータ"""

    file_path: str
    class_name: str
    method_name: str | None = None
    imports: list[str] = Field(default_factory=list)
    class_signature: str = ""
    member_vars: list[str] = Field(default_factory=list)
    chunk_type: str = "method"  # "method" or "file"


class JavaChunk(BaseModel):
    """Javaコードチャンク"""

    content: str
    metadata: ChunkMetadata
    token_count: int = 0


class SearchResult(BaseModel):
    """ChromaDB検索結果"""

    chunk: JavaChunk
    score: float


class ConversationTurn(BaseModel):
    """会話の1ターン"""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatHistory(BaseModel):
    """会話履歴"""

    turns: list[ConversationTurn] = Field(default_factory=list)

    def add_turn(self, role: str, content: str) -> None:
        """ターンを追加する"""
        self.turns.append(ConversationTurn(role=role, content=content))

    def get_recent_turns(self, n: int) -> list[ConversationTurn]:
        """最新n件のターンを返す"""
        return self.turns[-n:] if len(self.turns) >= n else self.turns[:]

    def truncate_to(self, n_turns: int) -> None:
        """先頭から古いターンを削除してn_turns件に切り詰める"""
        if len(self.turns) > n_turns:
            self.turns = self.turns[-n_turns:]


class ProjectInfo(BaseModel):
    """登録済みプロジェクトの情報"""

    name: str
    path: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProjectRegistry(BaseModel):
    """全プロジェクトのレジストリ"""

    projects: dict[str, ProjectInfo] = Field(default_factory=dict)
