from typing import List

from ollama import Client

from ..schemas.models import OllamaConfig


class OllamaEmbed:
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.client = Client(host=config.base_url)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            response = self.client.embeddings(
                model=self.config.embed_model, prompt=text
            )
            embeddings.append(response.get("embedding", []))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embeddings(model=self.config.embed_model, prompt=text)
        return response.get("embedding", [])
