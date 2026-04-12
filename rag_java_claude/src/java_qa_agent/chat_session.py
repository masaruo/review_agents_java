"""ChatSessionモジュール

マルチターン対話ループを管理する。
起動時チェック（Ollama接続・モデル存在・インデックス存在）を実行し、
対話ループでユーザーの質問に回答する。
"""

import sys

from java_qa_agent.backends.ollama_llm import LLMBackend
from java_qa_agent.context_builder import ContextBuilder
from java_qa_agent.logger import SessionLogger
from java_qa_agent.retriever import Retriever
from java_qa_agent.schemas.models import AppConfig, ChatHistory, ConversationTurn


class ChatSession:
    """マルチターン対話セッションを管理するクラス"""

    def __init__(
        self,
        project_name: str,
        config: AppConfig,
        llm: LLMBackend,
        retriever: Retriever,
        logger: SessionLogger,
    ) -> None:
        """初期化

        Args:
            project_name: 対話対象のプロジェクト名
            config: アプリケーション設定
            llm: LLMバックエンド
            retriever: Retrieverインスタンス
            logger: セッションロガー
        """
        self.project_name = project_name
        self.config = config
        self.llm = llm
        self.retriever = retriever
        self.logger = logger
        self.history = ChatHistory()
        self._context_builder = ContextBuilder(
            java_version=config.java_version,
            max_input_tokens=config.rag.max_input_tokens,
        )

    def should_exit(self, user_input: str) -> bool:
        """ユーザー入力が終了コマンドかどうかを判定する

        Args:
            user_input: ユーザーの入力文字列

        Returns:
            終了コマンドの場合True
        """
        return user_input.strip().lower() in ("exit", "quit")

    def process_turn(self, question: str) -> str | None:
        """1ターンの対話を処理する

        Args:
            question: ユーザーの質問文

        Returns:
            LLMの回答文字列（エラー時はNoneまたはエラー文字列）
        """
        try:
            # 関連チャンクを取得
            chunks = self.retriever.retrieve(
                self.project_name,
                question,
                top_k=self.config.rag.top_k,
            )

            # コンテキストを構築
            prompt = self._context_builder.build(chunks, self.history, question)

            # LLMで回答を生成
            response = self.llm.generate(prompt)

            # 履歴に追加
            self.history.add_turn("user", question)
            self.history.add_turn("assistant", response)

            # 履歴を制限
            max_turns = self.config.rag.max_history_turns * 2  # user + assistant pairs
            if len(self.history.turns) > max_turns:
                self.history.truncate_to(max_turns)

            # ログを保存
            if self.config.storage.save_logs:
                self.logger.log_turn(ConversationTurn(role="user", content=question))
                self.logger.log_turn(ConversationTurn(role="assistant", content=response))

            return response

        except Exception as e:
            # LLMパースエラーなどはSTDERRに出力してセッションを継続
            print(f"エラー: {e}", file=sys.stderr)
            return None

    def start(self) -> None:
        """対話ループを開始する

        起動時チェックを実行し、成功した場合に対話ループを開始する。
        'exit' または 'quit' で終了する。
        """
        print(f"Java Q&A Agent - プロジェクト: {self.project_name}")
        print(f"Ollama: {self.config.ollama.model}")
        print("終了するには 'exit' または 'quit' を入力してください")
        print()

        while True:
            try:
                user_input = input("質問を入力してください: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nセッションを終了します")
                break

            if not user_input:
                continue

            if self.should_exit(user_input):
                print("セッションを終了します")
                break

            print("\n[検索中...]\n")
            response = self.process_turn(user_input)

            if response:
                print(response)
            else:
                print(
                    "回答の生成中にエラーが発生しました。もう一度お試しください。", file=sys.stderr
                )

            print()
