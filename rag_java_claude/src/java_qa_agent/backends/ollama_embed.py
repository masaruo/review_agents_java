"""Ollamaエンベディングバックエンド

抽象インタフェース（EmbeddingBackend）とOllama実装（OllamaEmbedding）を提供する。
バッチ処理でOllamaへのリクエスト回数を最小化する。
"""

from abc import ABC, abstractmethod

import ollama


class EmbeddingBackend(ABC):
    """エンベディングバックエンドの抽象インタフェース"""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """テキストリストをバッチでエンベディングする

        Args:
            texts: エンベディングするテキストのリスト

        Returns:
            各テキストのベクトル表現のリスト
        """
        ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """1件のテキストをエンベディングする

        Args:
            text: エンベディングするテキスト

        Returns:
            ベクトル表現
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


class OllamaEmbedding(EmbeddingBackend):
    """Ollamaエンベディング実装

    ollama Python SDKを使用してOllamaサーバーと通信する。
    バッチ処理をサポートし、リクエスト回数を最小化する。
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout_seconds: int = 120,
    ) -> None:
        """初期化

        Args:
            base_url: OllamaサーバーのURL
            model: 使用するエンベディングモデル名
            timeout_seconds: タイムアウト（秒）
        """
        self.base_url = base_url
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._client = ollama.Client(host=base_url)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """テキストリストをバッチでエンベディングする

        Ollamaへのリクエストを1件ずつ発行する（Ollamaはバッチエンベディングに
        対応していないため、ループで処理する）。

        Args:
            texts: エンベディングするテキストのリスト

        Returns:
            各テキストのベクトル表現のリスト
        """
        embeddings: list[list[float]] = []
        for text in texts:
            embedding = self.embed_query(text)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        """1件のテキストをエンベディングする

        Args:
            text: エンベディングするテキスト

        Returns:
            ベクトル表現
        """
        response = self._client.embeddings(model=self.model, prompt=text)
        # レスポンスの形式に対応
        if isinstance(response, dict):
            return list(response.get("embedding", []))
        return list(response.embedding)  # type: ignore[union-attr]

    def check_model_available(self, model_name: str) -> bool:
        """指定モデルが利用可能かチェックする

        Args:
            model_name: チェックするモデル名

        Returns:
            モデルが存在する場合True、存在しない場合False
        """
        try:
            response = self._client.list()
            models = response.get("models", []) if isinstance(response, dict) else []
            if not models and hasattr(response, "models"):
                models = response.models  # type: ignore[union-attr]
            model_names = [
                m.get("name", "") if isinstance(m, dict) else getattr(m, "model", "")
                for m in models
            ]
            return any(
                name == model_name or name.startswith(model_name.split(":")[0])
                for name in model_names
            )
        except Exception:
            return False
