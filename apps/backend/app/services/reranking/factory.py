from typing import List
from app.services.retrieval.retriever import RetrievedCandidate
from app.services.reranking.base import BaseReranker
from app.services.reranking.cross_encoder import CrossEncoderReranker


class PassthroughReranker(BaseReranker):
    """Fallback reranker when reranking is disabled in the RAG configuration."""
    async def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 5
    ) -> List[RetrievedCandidate]:
        for rank, cand in enumerate(candidates, start=1):
            cand.rerank_score = None
            cand.reranked_rank = rank
        return candidates[:top_k]


def get_reranker(enabled: bool = True, model_name: str = "BAAI/bge-reranker-base") -> BaseReranker:
    if not enabled:
        return PassthroughReranker()
    return CrossEncoderReranker(model_name=model_name)
