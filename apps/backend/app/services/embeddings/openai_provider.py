from typing import List, Optional
import httpx
from app.core.config import settings
from app.services.embeddings.base import BaseEmbeddingProvider
from app.services.embeddings.local_provider import LocalEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_name: str = "text-embedding-3-small", api_key: Optional[str] = None):
        self._model_name = model_name
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._fallback = LocalEmbeddingProvider(model_name=model_name, dimension=1536)

    @property
    def dimension(self) -> int:
        return 1536 if "small" in self._model_name else 3072

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            # Fallback when key is not configured in local environment
            return await self._fallback.embed_documents(texts)

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                url,
                headers=headers,
                json={"input": texts, "model": self._model_name}
            )
            res.raise_for_status()
            data = res.json()
            return [item["embedding"] for item in data["data"]]

    async def embed_query(self, text: str) -> List[float]:
        res = await self.embed_documents([text])
        return res[0]
