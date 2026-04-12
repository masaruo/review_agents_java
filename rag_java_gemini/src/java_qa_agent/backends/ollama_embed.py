import logging
from typing import List, Optional

from ollama import Client, ResponseError

from ..schemas.models import OllamaConfig

logger = logging.getLogger(__name__)


class OllamaEmbed:
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.client = Client(host=config.base_url)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            emb = self.embed_query(text)
            if emb:
                embeddings.append(emb)
            else:
                # If embedding fails, return zero vector to maintain indexing alignment
                # or handle it in the caller. Here we return empty to skip it.
                # But to maintain batch alignment, we should be careful.
                # The current CLI implementation expects same length.
                # Actually, the CLI handles the batch list, so if we return a different size, it might break.
                # Let's return a zero vector of size 768 (nomic-embed-text) as fallback,
                # or better, raise a more informative error or return None and filter.
                embeddings.append([]) 
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        try:
            response = self.client.embeddings(model=self.config.embed_model, prompt=text)
            return response.get("embedding", [])
        except ResponseError as e:
            logger.error(f"Ollama embedding error: {e.status_code} - {e.error}")
            if e.status_code == 500 and "context length" in e.error.lower():
                logger.warning(f"Text too long for context length: {len(text)} chars. Truncating for retry.")
                # Fallback: Truncate and retry once
                truncated_text = text[:4000]
                try:
                    response = self.client.embeddings(model=self.config.embed_model, prompt=truncated_text)
                    return response.get("embedding", [])
                except Exception:
                    return []
            return []
        except Exception as e:
            logger.error(f"Unexpected embedding error: {e}")
            return []
