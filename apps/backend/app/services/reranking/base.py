from abc import ABC, abstractmethod
from typing import List
from app.services.retrieval.retriever import RetrievedCandidate


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 5
    ) -> List[RetrievedCandidate]:
        """
        Rerank a list of retrieved candidates based on deep cross-attention or relevance scoring.
        Assigns candidate.rerank_score and candidate.reranked_rank.
        """
        pass
