"""ChatSessionのユニットテスト"""

from unittest.mock import MagicMock

from java_qa_agent.chat_session import ChatSession
from java_qa_agent.schemas.models import AppConfig, OllamaConfig, RagConfig, StorageConfig


def make_test_config() -> AppConfig:
    """テスト用の設定を生成する"""
    return AppConfig(
        java_version=17,
        ollama=OllamaConfig(
            base_url="http://localhost:11434",
            model="qwen2.5-coder:7b",
            embed_model="nomic-embed-text",
            timeout_seconds=120,
        ),
        rag=RagConfig(
            top_k=5,
            chunk_token_threshold=1000,
            max_input_tokens=3000,
            max_history_turns=3,
        ),
        storage=StorageConfig(
            index_dir="/tmp/.indexes",
            log_dir="/tmp/.logs",
            save_logs=False,
        ),
    )


class TestChatSession:
    def _create_session_with_mocks(self) -> tuple[ChatSession, MagicMock, MagicMock, MagicMock]:
        """モック付きのChatSessionを生成する"""
        config = make_test_config()
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "これはテスト回答です"
        mock_llm.check_connection.return_value = True
        mock_llm.check_model_available.return_value = True

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []

        mock_logger = MagicMock()

        session = ChatSession(
            project_name="test-project",
            config=config,
            llm=mock_llm,
            retriever=mock_retriever,
            logger=mock_logger,
        )
        return session, mock_llm, mock_retriever, mock_logger

    def test_history_maintained_across_turns(self) -> None:
        """複数ターンで履歴が保持されることを確認する"""
        session, mock_llm, mock_retriever, _ = self._create_session_with_mocks()

        session.process_turn("最初の質問")
        session.process_turn("2番目の質問")

        # 履歴に2ターン分のユーザー質問と回答が含まれること
        assert len(session.history.turns) == 4  # user + assistant * 2

    def test_history_truncated_to_max(self) -> None:
        """max_history_turnsを超えると古い履歴が削除されることを確認する"""
        session, _, _, _ = self._create_session_with_mocks()

        # max_history_turns=3なので、3ターン * 2（user + assistant）= 6
        for i in range(5):
            session.process_turn(f"質問{i}")

        # max_history_turns（3）を超えないことを確認
        # turns = user + assistant pairs
        max_turns = session.config.rag.max_history_turns * 2
        assert len(session.history.turns) <= max_turns

    def test_exits_on_exit_command(self) -> None:
        """'exit'入力でループが終了することを確認する"""
        session, _, _, _ = self._create_session_with_mocks()
        assert session.should_exit("exit") is True

    def test_exits_on_quit_command(self) -> None:
        """'quit'入力でループが終了することを確認する"""
        session, _, _, _ = self._create_session_with_mocks()
        assert session.should_exit("quit") is True

    def test_does_not_exit_on_normal_input(self) -> None:
        """通常の入力ではループが終了しないことを確認する"""
        session, _, _, _ = self._create_session_with_mocks()
        assert session.should_exit("addメソッドを教えてください") is False

    def test_exit_case_insensitive(self) -> None:
        """'EXIT'でもループが終了することを確認する"""
        session, _, _, _ = self._create_session_with_mocks()
        assert session.should_exit("EXIT") is True
        assert session.should_exit("Quit") is True

    def test_process_turn_returns_response(self) -> None:
        """process_turnがLLMの回答を返すことを確認する"""
        session, mock_llm, _, _ = self._create_session_with_mocks()
        mock_llm.generate.return_value = "テスト回答"

        response = session.process_turn("質問")
        assert response == "テスト回答"

    def test_process_turn_calls_retriever(self) -> None:
        """process_turnがRetrieverを呼ぶことを確認する"""
        session, _, mock_retriever, _ = self._create_session_with_mocks()
        mock_retriever.retrieve.return_value = []

        session.process_turn("質問")
        mock_retriever.retrieve.assert_called_once()

    def test_process_turn_calls_llm(self) -> None:
        """process_turnがLLMを呼ぶことを確認する"""
        session, mock_llm, _, _ = self._create_session_with_mocks()

        session.process_turn("質問")
        mock_llm.generate.assert_called_once()

    def test_logger_called_when_save_logs_true(self) -> None:
        """save_logs=Trueの場合にロガーが呼ばれることを確認する"""
        config = make_test_config()
        config.storage.save_logs = True
        mock_llm = MagicMock()
        mock_llm.generate.return_value = "回答"
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = []
        mock_logger = MagicMock()

        session = ChatSession(
            project_name="test-project",
            config=config,
            llm=mock_llm,
            retriever=mock_retriever,
            logger=mock_logger,
        )
        session.process_turn("質問")
        mock_logger.log_turn.assert_called()

    def test_llm_error_continues_session(self) -> None:
        """LLMエラー時にセッションが継続されることを確認する"""
        session, mock_llm, _, _ = self._create_session_with_mocks()
        mock_llm.generate.side_effect = ValueError("LLMパースエラー")

        # エラーが発生してもセッションが終了しないこと
        result = session.process_turn("質問")
        # エラー時はNoneまたはエラーメッセージを返す
        assert result is None or isinstance(result, str)
