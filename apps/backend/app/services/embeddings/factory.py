from app.services.embeddings.base import BaseEmbeddingProvider
from app.services.embeddings.local_provider import LocalEmbeddingProvider
from app.services.embeddings.openai_provider import OpenAIEmbeddingProvider


def get_embedding_provider(model_name: str = "text-embedding-3-small") -> BaseEmbeddingProvider:
    name = (model_name or "text-embedding-3-small").strip()
    if name.startswith("text-embedding"):
        return OpenAIEmbeddingProvider(model_name=name)
    elif "bge" in name or "minilm" in name or "local" in name:
        dim = 1024 if "large" in name else 384
        return LocalEmbeddingProvider(model_name=name, dimension=dim)
    else:
        # Default to local provider with 384 dimensions
        return LocalEmbeddingProvider(model_name=name, dimension=384)
