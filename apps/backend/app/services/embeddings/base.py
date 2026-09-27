from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the generated vector embeddings."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier name of the embedding model."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute vector embeddings for a batch of text documents."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> List[float]:
        """Compute vector embedding for a single search query."""
        pass
