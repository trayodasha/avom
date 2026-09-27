import enum
from typing import List, Dict, Any, Optional


class FailureCategory(str, enum.Enum):
    NO_RELEVANT_CONTEXT = "NO_RELEVANT_CONTEXT"
    BAD_RETRIEVAL = "BAD_RETRIEVAL"
    BAD_RERANKING = "BAD_RERANKING"
    HALLUCINATION = "HALLUCINATION"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    WRONG_CITATION = "WRONG_CITATION"
    SUCCESS = "SUCCESS"


class FailureClassifier:
    """
    Automated root cause diagnostic engine for RAG query failures.
    Analyzes intermediate retrieval scores, reranking positions, faithfulness,
    and citation alignments to pinpoint the exact failure stage.
    """

    @classmethod
    def diagnose(
        cls,
        scores: Dict[str, float],
        retrieved_chunk_count: int,
        has_citations: bool,
        dense_scores: Optional[List[float]] = None,
        rerank_scores: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        faithfulness = scores.get("faithfulness", 1.0)
        recall = scores.get("recall@k", 1.0)
        relevance = scores.get("answer_relevance", 1.0)

        # 1. Zero chunks retrieved
        if retrieved_chunk_count == 0:
            return {
                "category": FailureCategory.NO_RELEVANT_CONTEXT.value,
                "reason": "Retriever returned 0 chunks exceeding relevance threshold.",
                "remedy": "Lower similarity cutoffs, verify corpus embedding coverage, or enhance BM25 tokenization."
            }

        # 2. Retrieval recall dropped
        if recall < 0.3:
            return {
                "category": FailureCategory.BAD_RETRIEVAL.value,
                "reason": "Dense and BM25 retrievers failed to capture ground truth context in initial top-K.",
                "remedy": "Experiment with hybrid fusion weights, recursive chunking, or semantic chunking."
            }

        # 3. Reranker dropped top candidates
        if dense_scores and rerank_scores:
            if max(dense_scores) > 0.8 and max(rerank_scores) < 0.3:
                return {
                    "category": FailureCategory.BAD_RERANKING.value,
                    "reason": "Cross-encoder reranker heavily discounted candidates that dense retrieval ranked highly.",
                    "remedy": "Tune cross-encoder model checkpoint or adjust candidate K window."
                }

        # 4. Hallucination / Low Faithfulness
        if faithfulness < 0.6:
            return {
                "category": FailureCategory.HALLUCINATION.value,
                "reason": "LLM synthesized factual claims unsupported by the retrieved context.",
                "remedy": "Strengthen system grounding prompt, decrease temperature to 0.0, or use a larger reasoning model."
            }

        # 5. Low Answer Relevance
        if relevance < 0.5:
            return {
                "category": FailureCategory.INSUFFICIENT_CONTEXT.value,
                "reason": "Response did not directly address the query despite high chunk scores.",
                "remedy": "Ensure context chunks encompass the user's specific operational question."
            }

        # 6. Citations missing despite claims
        if not has_citations and len(scores) > 0:
            return {
                "category": FailureCategory.WRONG_CITATION.value,
                "reason": "Synthesis failed to attribute context chunks using bracketed citation markers.",
                "remedy": "Enforce citation few-shot examples in system prompt."
            }

        return {
            "category": FailureCategory.SUCCESS.value,
            "reason": "Pipeline passed all quality and groundedness constraints.",
            "remedy": "Optimal performance."
        }
