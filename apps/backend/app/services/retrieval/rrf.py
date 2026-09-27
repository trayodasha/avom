from typing import List, Dict, Any, Tuple


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) algorithm to combine rankings from multiple retrieval channels
    (e.g. dense vector search and sparse BM25 search).
    Formula:
        RRF_score(d) = sum_r ( w_r / (k + rank_r(d)) )
    """
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        dense_results: List[Tuple[str, float]],   # [(chunk_id, cosine_score)]
        sparse_results: List[Tuple[str, float]],  # [(chunk_id, bm25_score)]
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Merges dense and sparse rankings and returns scored items with rank provenance.
        """
        combined: Dict[str, Dict[str, Any]] = {}

        # Process dense rankings
        for rank, (chunk_id, score) in enumerate(dense_results, start=1):
            if chunk_id not in combined:
                combined[chunk_id] = {
                    "chunk_id": chunk_id,
                    "dense_score": float(score),
                    "sparse_score": 0.0,
                    "dense_rank": rank,
                    "sparse_rank": None,
                    "rrf_score": 0.0,
                }
            else:
                combined[chunk_id]["dense_score"] = float(score)
                combined[chunk_id]["dense_rank"] = rank

            combined[chunk_id]["rrf_score"] += dense_weight / (self.k + rank)

        # Process sparse rankings
        for rank, (chunk_id, score) in enumerate(sparse_results, start=1):
            if chunk_id not in combined:
                combined[chunk_id] = {
                    "chunk_id": chunk_id,
                    "dense_score": 0.0,
                    "sparse_score": float(score),
                    "dense_rank": None,
                    "sparse_rank": rank,
                    "rrf_score": 0.0,
                }
            else:
                combined[chunk_id]["sparse_score"] = float(score)
                combined[chunk_id]["sparse_rank"] = rank

            combined[chunk_id]["rrf_score"] += sparse_weight / (self.k + rank)

        # Sort by final RRF score descending
        ranked_items = sorted(
            combined.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        # Assign initial fused rank
        for i, item in enumerate(ranked_items, start=1):
            item["initial_rank"] = i

        return ranked_items[:top_k]
