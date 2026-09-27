import pytest
from app.services.evaluation.metrics import RetrievalMetrics
from app.services.evaluation.judge import LLMJudge


def test_retrieval_recall_at_k():
    ground_truth = ["doc-1", "doc-2", "doc-3"]
    retrieved = ["doc-1", "doc-99", "doc-2", "doc-88", "doc-77"]

    # Top-3 has doc-1 and doc-2 (2 out of 3 ground truth)
    recall_3 = RetrievalMetrics.recall_at_k(retrieved, ground_truth, k=3)
    assert round(recall_3, 4) == round(2 / 3, 4)

    # Top-5 has doc-1 and doc-2
    recall_5 = RetrievalMetrics.recall_at_k(retrieved, ground_truth, k=5)
    assert round(recall_5, 4) == round(2 / 3, 4)

    # Top-1 has only doc-1
    recall_1 = RetrievalMetrics.recall_at_k(retrieved, ground_truth, k=1)
    assert round(recall_1, 4) == round(1 / 3, 4)


def test_retrieval_precision_at_k():
    ground_truth = ["doc-1", "doc-2"]
    retrieved = ["doc-1", "doc-99", "doc-2", "doc-88"]

    # Top-2 has 1 hit out of 2 retrieved => 0.5
    assert RetrievalMetrics.precision_at_k(retrieved, ground_truth, k=2) == 0.5

    # Top-4 has 2 hits out of 4 retrieved => 0.5
    assert RetrievalMetrics.precision_at_k(retrieved, ground_truth, k=4) == 0.5


def test_retrieval_mrr():
    ground_truth = ["target-doc"]
    
    # Hit at rank 1 => 1.0
    assert RetrievalMetrics.mrr(["target-doc", "other"], ground_truth) == 1.0

    # Hit at rank 2 => 0.5
    assert RetrievalMetrics.mrr(["other", "target-doc"], ground_truth) == 0.5

    # Hit at rank 4 => 0.25
    assert RetrievalMetrics.mrr(["a", "b", "c", "target-doc"], ground_truth) == 0.25

    # No hit => 0.0
    assert RetrievalMetrics.mrr(["a", "b", "c"], ground_truth) == 0.0


def test_retrieval_ndcg():
    ground_truth = ["doc-1", "doc-2"]
    
    # Perfect order
    perfect = ["doc-1", "doc-2", "doc-3"]
    assert RetrievalMetrics.ndcg_at_k(perfect, ground_truth, k=3) == 1.0

    # Inverted order
    inverted = ["doc-99", "doc-1", "doc-2"]
    ndcg_val = RetrievalMetrics.ndcg_at_k(inverted, ground_truth, k=3)
    assert 0.0 < ndcg_val < 1.0


@pytest.mark.asyncio
async def test_llm_judge_deterministic_metrics():
    judge = LLMJudge(model_name="local-deterministic")
    context = [
        "PostgreSQL is an open-source relational database emphasizing SQL compliance.",
        "Qdrant provides high-speed vector similarity indexing with HNSW graphs."
    ]

    # Faithful answer
    faithful_answer = "PostgreSQL is an open-source relational database that complies with SQL standards."
    f_score = await judge.evaluate_faithfulness("What is PostgreSQL?", faithful_answer, context)
    assert f_score >= 0.5

    # Answer relevance
    rel_score = await judge.evaluate_answer_relevance("What is PostgreSQL?", faithful_answer)
    assert rel_score >= 0.5

    # Context recall
    ctx_rec = await judge.evaluate_context_recall(
        ground_truth="PostgreSQL complies with SQL compliance and Qdrant provides vector similarity.",
        context_chunks=context
    )
    assert ctx_rec >= 0.5
