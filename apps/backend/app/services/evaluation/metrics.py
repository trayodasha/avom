import math
from typing import List, Set, Any


class RetrievalMetrics:
    """
    Standard information retrieval evaluation metrics computed against
    ground truth relevance sets.
    """

    @staticmethod
    def recall_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
        """
        Fraction of relevant documents retrieved in top-k.
        Recall@K = |Retrieved@K ∩ GroundTruth| / |GroundTruth|
        """
        if not ground_truth_ids:
            return 1.0 if not retrieved_ids else 0.0
        
        top_k = retrieved_ids[:k]
        gt_set = set(ground_truth_ids)
        hits = len(set(top_k).intersection(gt_set))
        return hits / len(gt_set)

    @staticmethod
    def precision_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
        """
        Fraction of retrieved top-k documents that are relevant.
        Precision@K = |Retrieved@K ∩ GroundTruth| / K
        """
        if k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        if not top_k:
            return 0.0
        gt_set = set(ground_truth_ids)
        hits = len(set(top_k).intersection(gt_set))
        return hits / len(top_k)

    @staticmethod
    def mrr(retrieved_ids: List[str], ground_truth_ids: List[str]) -> float:
        """
        Reciprocal Rank of the first relevant document retrieved.
        RR = 1 / rank_first_hit
        """
        if not ground_truth_ids or not retrieved_ids:
            return 0.0
        gt_set = set(ground_truth_ids)
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in gt_set:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def hit_rate_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
        """
        Binary indicator: 1.0 if any ground truth document is in top-k, 0.0 otherwise.
        """
        if not ground_truth_ids:
            return 0.0
        top_k = set(retrieved_ids[:k])
        gt_set = set(ground_truth_ids)
        return 1.0 if len(top_k.intersection(gt_set)) > 0 else 0.0

    @staticmethod
    def ndcg_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 5) -> float:
        """
        Normalized Discounted Cumulative Gain at rank K.
        DCG@K = sum_{i=1}^K (rel_i / log2(i + 1))
        IDCG@K = sum_{i=1}^{min(K, |GT|)} (1 / log2(i + 1))
        NDCG@K = DCG / IDCG
        """
        if not ground_truth_ids or not retrieved_ids or k <= 0:
            return 0.0

        gt_set = set(ground_truth_ids)
        top_k = retrieved_ids[:k]

        # Calculate DCG
        dcg = 0.0
        for i, doc_id in enumerate(top_k, start=1):
            rel = 1.0 if doc_id in gt_set else 0.0
            if rel > 0:
                dcg += rel / math.log2(i + 1)

        # Calculate Ideal DCG (IDCG)
        ideal_hits = min(k, len(gt_set))
        if ideal_hits == 0:
            return 0.0

        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
        return dcg / idcg if idcg > 0 else 0.0

    @staticmethod
    def map_score(retrieved_ids: List[str], ground_truth_ids: List[str], k: int = 10) -> float:
        """
        Mean Average Precision for a single query.
        AP = sum_{i=1}^k (Precision@i * rel_i) / |GroundTruth|
        """
        if not ground_truth_ids or not retrieved_ids or k <= 0:
            return 0.0

        gt_set = set(ground_truth_ids)
        top_k = retrieved_ids[:k]
        cumulative_hits = 0
        sum_precisions = 0.0

        for i, doc_id in enumerate(top_k, start=1):
            if doc_id in gt_set:
                cumulative_hits += 1
                sum_precisions += cumulative_hits / i

        return sum_precisions / min(k, len(gt_set)) if len(gt_set) > 0 else 0.0
