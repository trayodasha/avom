import logging
from typing import Optional
from qdrant_client import QdrantClient
from app.core.config import settings

logger = logging.getLogger(__name__)

_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        if settings.QDRANT_URL:
            logger.info(f"Connecting to Qdrant at {settings.QDRANT_URL}")
            _qdrant_client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=10.0
            )
        else:
            logger.info("Initializing in-memory / local Qdrant instance for development")
            _qdrant_client = QdrantClient(location=":memory:")
    return _qdrant_client


def check_qdrant_health() -> bool:
    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception as e:
        logger.warning(f"Qdrant health check failed: {e}")
        return False
