import json
import ollama
from typing import Dict, Any, Optional

class OllamaBackend:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)

    def check_connection(self) -> bool:
        """Ollama サーバーへの接続確認とモデルの存在確認。"""
        try:
            self.client.list()
            return True
        except Exception:
            return False

    def generate_json(self, model: str, prompt: str) -> Dict[str, Any]:
        """LLM から JSON 形式でレスポンスを取得する。"""
        try:
            response = self.client.generate(
                model=model,
                prompt=prompt,
                format="json",
                options={"temperature": 0}
            )
            return json.loads(response["response"])
        except Exception as e:
            # エラー発生時は呼び出し元で処理（Skipped 記録）
            raise e
