"""Ollama LLMバックエンド

抽象インタフェース（LLMBackend）とOllama実装（OllamaLLM）を提供する。
将来的なモデルバックエンドの差し替えを容易にするための設計。
シリアル実行（Max Concurrency: 1）で動作する。
"""

from abc import ABC, abstractmethod

import ollama


class OllamaConnectionError(Exception):
    """Ollama接続エラー"""

    pass


class OllamaModelNotFoundError(Exception):
    """Ollamaモデル未取得エラー"""

    pass


class LLMBackend(ABC):
    """LLMバックエンドの抽象インタフェース"""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """プロンプトからテキストを生成する

        Args:
            prompt: 入力プロンプト

        Returns:
            生成されたテキスト
        """
        ...

    @abstractmethod
    def check_connection(self) -> bool:
        """Ollamaサーバーへの接続を確認する

        Returns:
            接続成功の場合True、失敗の場合False
        """
        ...

    @abstractmethod
    def check_model_available(self, model_name: str) -> bool:
        """指定モデルが利用可能かチェックする

        Args:
            model_name: チェックするモデル名

        Returns:
            モデルが存在する場合True、存在しない場合False
        """
        ...


class OllamaLLM(LLMBackend):
    """Ollama LLM実装

    ollama Python SDKを使用してOllamaサーバーと通信する。
    シリアル実行で動作する（並列化なし）。
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5-coder:7b",
        timeout_seconds: int = 120,
    ) -> None:
        """初期化

        Args:
            base_url: OllamaサーバーのURL
            model: 使用するモデル名
            timeout_seconds: タイムアウト（秒）
        """
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = ollama.Client(host=base_url)

    def generate(self, prompt: str) -> str:
        """プロンプトからテキストを生成する

        Args:
            prompt: 入力プロンプト

        Returns:
            生成されたテキスト

        Raises:
            OllamaConnectionError: Ollama接続失敗時
        """
        try:
            response = self._client.generate(
                model=self.model,
                prompt=prompt,
            )
            return str(response.response)
        except Exception as e:
            if "Connection" in str(e) or "refused" in str(e).lower():
                raise OllamaConnectionError(
                    f"Ollamaサーバーへの接続に失敗しました: {self.base_url}"
                ) from e
            raise

    def check_connection(self) -> bool:
        """Ollamaサーバーへの接続を確認する

        Returns:
            接続成功の場合True、失敗の場合False
        """
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def check_model_available(self, model_name: str) -> bool:
        """指定モデルが利用可能かチェックする

        Args:
            model_name: チェックするモデル名

        Returns:
            モデルが存在する場合True、存在しない場合False
        """
        try:
            response = self._client.list()
            # ollama SDKのレスポンス形式に対応
            models = response.get("models", []) if isinstance(response, dict) else []
            if not models and hasattr(response, "models"):
                models = response.models  # type: ignore[union-attr]
            model_names = [
                m.get("name", "") if isinstance(m, dict) else getattr(m, "model", "")
                for m in models
            ]
            # モデル名の完全一致または前方一致でチェック
            return any(
                name == model_name or name.startswith(model_name.split(":")[0])
                for name in model_names
            )
        except Exception:
            return False
