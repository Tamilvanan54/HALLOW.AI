import requests
from typing import List
from concurrent.futures import ThreadPoolExecutor
from langchain_core.embeddings import Embeddings
from app.config import DEFAULT_EMBEDDING_MODEL, OLLAMA_BASE_URL


class OllamaNativeEmbeddings(Embeddings):
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL, base_url: str = OLLAMA_BASE_URL, max_workers: int = 8):
        self.model_name = model_name
        self.url = f"{base_url}/api/embeddings"
        self.max_workers = max_workers

    def _get_embedding(self, text: str) -> List[float]:
        try:
            response = requests.post(
                self.url,
                json={"model": self.model_name, "prompt": text, "keep_alive": "24h"},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                raise RuntimeError(f"Ollama error status code: {response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Could not fetch embedding from Ollama: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(self._get_embedding, texts))

    def embed_query(self, text: str) -> List[float]:
        return self._get_embedding(text)