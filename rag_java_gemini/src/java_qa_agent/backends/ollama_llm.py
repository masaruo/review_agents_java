from typing import List

from ollama import Client

from ..schemas.models import OllamaConfig


class OllamaLLM:
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.client = Client(host=config.base_url)

    def generate(self, prompt: str) -> str:
        response = self.client.generate(model=self.config.model, prompt=prompt)
        return response.get("response", "")

    def check_connection(self) -> bool:
        try:
            models_list = self.client.list()
            # Convert models list to names if it's a list of dicts or objects
            # Ollama Python SDK returns a dict with 'models' key
            # Each model might be a dict or an object with 'name' or 'model' attribute
            models = models_list.get("models", [])
            model_names = []
            for m in models:
                if isinstance(m, dict):
                    model_names.append(m.get("name", m.get("model", "")))
                else:
                    model_names.append(getattr(m, "name", getattr(m, "model", "")))

            # Use basic name matching or full name matching (with :latest)
            def match_model(target: str, existing: List[str]) -> bool:
                for name in existing:
                    if (
                        target == name
                        or f"{target}:latest" == name
                        or target == name.split(":")[0]
                    ):
                        return True
                return False

            return match_model(self.config.model, model_names) and match_model(
                self.config.embed_model, model_names
            )
        except Exception:
            return False
