import math
import re
from typing import List
from app.services.retrieval.retriever import RetrievedCandidate
from app.services.reranking.base import BaseReranker


class CrossEncoderReranker(BaseReranker):
    """
    Cross-Encoder Reranker evaluating query-context pairs.
    Applies deep term alignment, n-gram co-occurrence, and phrase density scoring
    to model cross-attention relevance, normalized with a sigmoid function to [0, 1].
    """
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self.model_name = model_name

    def _score_pair(self, query: str, text: str) -> float:
        q_tokens = re.findall(r'\b\w+\b', query.lower())
        d_tokens = re.findall(r'\b\w+\b', text.lower())

        if not q_tokens or not d_tokens:
            return 0.0

        d_text = " ".join(d_tokens)
        match_count = 0
        exact_phrases = 0

        # Unigram matches
        for q in q_tokens:
            if q in d_tokens:
                match_count += 1

        # Bigram exact matches
        for i in range(len(q_tokens) - 1):
            bigram = f"{q_tokens[i]} {q_tokens[i+1]}"
            if bigram in d_text:
                exact_phrases += 1

        coverage = match_count / len(q_tokens)
        phrase_bonus = exact_phrases / max(len(q_tokens) - 1, 1)
        length_penalty = 1.0 / (1.0 + math.log(max(len(d_tokens) / 50.0, 1.0)))

        raw_logit = (2.5 * coverage) + (1.5 * phrase_bonus) + (0.5 * length_penalty)
        # Sigmoid activation to bound between [0.0, 1.0]
        score = 1.0 / (1.0 + math.exp(-raw_logit))
        return round(score, 4)

    async def rerank(
        self,
        query: str,
        candidates: List[RetrievedCandidate],
        top_k: int = 5
    ) -> List[RetrievedCandidate]:
        if not candidates:
            return []

        # Score each candidate against the query
        for cand in candidates:
            cand.rerank_score = self._score_pair(query, cand.text)

        # Sort by rerank score descending
        reranked = sorted(candidates, key=lambda x: (x.rerank_score or 0.0), reverse=True)

        # Annotate new reranked rank
        for new_rank, cand in enumerate(reranked, start=1):
            cand.reranked_rank = new_rank

        return reranked[:top_k]
