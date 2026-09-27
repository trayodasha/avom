import math
import hashlib
from typing import List
from app.services.embeddings.base import BaseEmbeddingProvider


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic zero-dependency local embedding provider.
    Constructs normalized dense feature vectors across token hash projections.
    Ideal for local developer environments, testing, and offline benchmarking.
    """
    def __init__(self, model_name: str = "bge-small-en-v1.5", dimension: int = 384):
        self._model_name = model_name
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_vector(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dimension

        vec = [0.0] * self._dimension
        tokens = text.lower().split()
        
        # Word-level and character n-gram feature hashing
        for i, token in enumerate(tokens):
            weight = 1.0 / math.sqrt(i + 1)
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dimension
            sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
            vec[idx] += sign * weight

            # Bigram feature
            if i > 0:
                bigram = f"{tokens[i-1]}_{token}"
                hb = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                b_idx = hb % self._dimension
                b_sign = 1.0 if (hb >> 1) % 2 == 0 else -1.0
                vec[b_idx] += b_sign * 0.5

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            return [x / norm for x in vec]
        return [0.0] * self._dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]

    async def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)
