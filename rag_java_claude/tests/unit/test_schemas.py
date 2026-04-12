"""Pydanticモデルのユニットテスト"""

from datetime import datetime

from java_qa_agent.schemas.models import (
    AppConfig,
    ChatHistory,
    ChunkMetadata,
    ConversationTurn,
    JavaChunk,
    OllamaConfig,
    ProjectInfo,
    ProjectRegistry,
    RagConfig,
    SearchResult,
    StorageConfig,
)


class TestOllamaConfig:
    def test_default_values(self) -> None:
        """デフォルト値が正しいことを確認する"""
        config = OllamaConfig()
        assert config.base_url == "http://localhost:11434"
        assert config.model == "qwen2.5-coder:7b"
        assert config.embed_model == "nomic-embed-text"
        assert config.timeout_seconds == 120

    def test_custom_values(self) -> None:
        """カスタム値が正しく設定されることを確認する"""
        config = OllamaConfig(
            base_url="http://remote:11434",
            model="llama3:8b",
            embed_model="mxbai-embed-large",
            timeout_seconds=60,
        )
        assert config.base_url == "http://remote:11434"
        assert config.model == "llama3:8b"
        assert config.timeout_seconds == 60


class TestRagConfig:
    def test_default_values(self) -> None:
        """デフォルト値が正しいことを確認する"""
        config = RagConfig()
        assert config.top_k == 5
        assert config.chunk_token_threshold == 1000
        assert config.max_input_tokens == 3000
        assert config.max_history_turns == 6

    def test_custom_values(self) -> None:
        """カスタム値が正しく設定されることを確認する"""
        config = RagConfig(top_k=10, max_input_tokens=5000)
        assert config.top_k == 10
        assert config.max_input_tokens == 5000


class TestStorageConfig:
    def test_default_values(self) -> None:
        """デフォルト値が正しいことを確認する"""
        config = StorageConfig()
        assert config.index_dir == "~/.java_qa_agent/indexes"
        assert config.log_dir == "~/.java_qa_agent/logs"
        assert config.save_logs is True

    def test_save_logs_false(self) -> None:
        """save_logsをFalseに設定できることを確認する"""
        config = StorageConfig(save_logs=False)
        assert config.save_logs is False


class TestAppConfig:
    def test_default_values(self) -> None:
        """デフォルト値が正しいことを確認する"""
        config = AppConfig()
        assert config.java_version == 17
        assert isinstance(config.ollama, OllamaConfig)
        assert isinstance(config.rag, RagConfig)
        assert isinstance(config.storage, StorageConfig)

    def test_from_dict(self) -> None:
        """dictから生成できることを確認する"""
        data = {
            "java_version": 21,
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5-coder:7b",
                "embed_model": "nomic-embed-text",
                "timeout_seconds": 120,
            },
            "rag": {
                "top_k": 3,
                "chunk_token_threshold": 500,
                "max_input_tokens": 2000,
                "max_history_turns": 4,
            },
            "storage": {
                "index_dir": "~/.java_qa_agent/indexes",
                "log_dir": "~/.java_qa_agent/logs",
                "save_logs": False,
            },
        }
        config = AppConfig(**data)
        assert config.java_version == 21
        assert config.rag.top_k == 3
        assert config.storage.save_logs is False

    def test_nested_config_accessible(self) -> None:
        """ネストされた設定にアクセスできることを確認する"""
        config = AppConfig()
        assert config.ollama.model == "qwen2.5-coder:7b"
        assert config.rag.top_k == 5


class TestChunkMetadata:
    def test_creation(self) -> None:
        """ChunkMetadataが正しく生成できることを確認する"""
        metadata = ChunkMetadata(
            file_path="/path/to/Calculator.java",
            class_name="Calculator",
            method_name="add",
            imports=["import java.util.List;"],
            class_signature="public class Calculator",
            member_vars=["private int result;"],
            chunk_type="method",
        )
        assert metadata.file_path == "/path/to/Calculator.java"
        assert metadata.class_name == "Calculator"
        assert metadata.method_name == "add"
        assert metadata.chunk_type == "method"

    def test_default_values(self) -> None:
        """デフォルト値が正しいことを確認する"""
        metadata = ChunkMetadata(
            file_path="/path/to/File.java",
            class_name="File",
        )
        assert metadata.method_name is None
        assert metadata.imports == []
        assert metadata.class_signature == ""
        assert metadata.member_vars == []
        assert metadata.chunk_type == "method"

    def test_file_chunk_type(self) -> None:
        """chunk_typeにfileを設定できることを確認する"""
        metadata = ChunkMetadata(
            file_path="/path/to/File.java",
            class_name="File",
            chunk_type="file",
        )
        assert metadata.chunk_type == "file"


class TestJavaChunk:
    def test_creation(self) -> None:
        """JavaChunkが正しく生成できることを確認する"""
        metadata = ChunkMetadata(
            file_path="/path/to/Calculator.java",
            class_name="Calculator",
            method_name="add",
        )
        chunk = JavaChunk(
            content="public int add(int a, int b) { return a + b; }",
            metadata=metadata,
            token_count=15,
        )
        assert chunk.content == "public int add(int a, int b) { return a + b; }"
        assert chunk.token_count == 15
        assert chunk.metadata.class_name == "Calculator"

    def test_serialization(self) -> None:
        """JSONシリアライゼーションが正しいことを確認する"""
        metadata = ChunkMetadata(
            file_path="/path/to/Calculator.java",
            class_name="Calculator",
        )
        chunk = JavaChunk(content="public class Calculator {}", metadata=metadata)
        json_str = chunk.model_dump_json()
        assert "Calculator" in json_str
        assert "content" in json_str


class TestSearchResult:
    def test_creation(self) -> None:
        """SearchResultが正しく生成できることを確認する"""
        metadata = ChunkMetadata(
            file_path="/path/to/Calculator.java",
            class_name="Calculator",
        )
        chunk = JavaChunk(content="public class Calculator {}", metadata=metadata)
        result = SearchResult(chunk=chunk, score=0.85)
        assert result.score == 0.85
        assert result.chunk.metadata.class_name == "Calculator"


class TestConversationTurn:
    def test_user_turn(self) -> None:
        """ユーザーターンが正しく生成できることを確認する"""
        turn = ConversationTurn(role="user", content="addメソッドを教えてください")
        assert turn.role == "user"
        assert turn.content == "addメソッドを教えてください"
        assert isinstance(turn.timestamp, datetime)

    def test_assistant_turn(self) -> None:
        """アシスタントターンが正しく生成できることを確認する"""
        turn = ConversationTurn(role="assistant", content="addメソッドは...")
        assert turn.role == "assistant"

    def test_timestamp_auto_set(self) -> None:
        """タイムスタンプが自動設定されることを確認する"""
        turn = ConversationTurn(role="user", content="質問")
        assert isinstance(turn.timestamp, datetime)


class TestChatHistory:
    def test_empty_history(self) -> None:
        """空の履歴が正しく生成できることを確認する"""
        history = ChatHistory()
        assert history.turns == []

    def test_add_turn(self) -> None:
        """ターン追加が機能することを確認する"""
        history = ChatHistory()
        history.add_turn("user", "質問")
        history.add_turn("assistant", "回答")
        assert len(history.turns) == 2
        assert history.turns[0].role == "user"
        assert history.turns[1].role == "assistant"

    def test_get_recent_turns(self) -> None:
        """最新n件のターンを取得できることを確認する"""
        history = ChatHistory()
        for i in range(6):
            history.add_turn("user", f"質問{i}")
            history.add_turn("assistant", f"回答{i}")
        recent = history.get_recent_turns(4)
        assert len(recent) == 4
        assert recent[-1].content == "回答5"

    def test_truncate_to(self) -> None:
        """古いターンが正しく削除されることを確認する"""
        history = ChatHistory()
        history.add_turn("user", "質問1")
        history.add_turn("assistant", "回答1")
        history.add_turn("user", "質問2")
        history.add_turn("assistant", "回答2")
        history.add_turn("user", "質問3")
        history.add_turn("assistant", "回答3")

        history.truncate_to(4)
        assert len(history.turns) == 4
        # 最初の2ターンが削除されていることを確認
        assert history.turns[0].content == "質問2"

    def test_truncate_to_when_already_small(self) -> None:
        """既に制限以下の場合は何もしないことを確認する"""
        history = ChatHistory()
        history.add_turn("user", "質問")
        history.truncate_to(6)
        assert len(history.turns) == 1


class TestProjectInfo:
    def test_creation(self) -> None:
        """ProjectInfoが正しく生成できることを確認する"""
        info = ProjectInfo(name="my-project", path="/path/to/project")
        assert info.name == "my-project"
        assert info.path == "/path/to/project"
        assert isinstance(info.created_at, datetime)
        assert isinstance(info.updated_at, datetime)


class TestProjectRegistry:
    def test_empty_registry(self) -> None:
        """空のレジストリが正しく生成できることを確認する"""
        registry = ProjectRegistry()
        assert registry.projects == {}

    def test_add_project(self) -> None:
        """プロジェクト追加が機能することを確認する"""
        registry = ProjectRegistry()
        info = ProjectInfo(name="my-project", path="/path/to/project")
        registry.projects["my-project"] = info
        assert "my-project" in registry.projects
        assert registry.projects["my-project"].name == "my-project"

    def test_serialization(self) -> None:
        """JSONシリアライゼーションが正しいことを確認する"""
        registry = ProjectRegistry()
        info = ProjectInfo(name="my-project", path="/path/to/project")
        registry.projects["my-project"] = info
        json_str = registry.model_dump_json()
        assert "my-project" in json_str
        assert "/path/to/project" in json_str

    def test_deserialization(self) -> None:
        """JSONデシリアライゼーションが正しいことを確認する"""
        registry = ProjectRegistry()
        info = ProjectInfo(name="my-project", path="/path/to/project")
        registry.projects["my-project"] = info

        json_str = registry.model_dump_json()
        restored = ProjectRegistry.model_validate_json(json_str)
        assert "my-project" in restored.projects
        assert restored.projects["my-project"].path == "/path/to/project"
