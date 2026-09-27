import pytest
from app.services.retrieval.retriever import RetrievedCandidate
from app.services.reranking.cross_encoder import CrossEncoderReranker
from app.services.reranking.factory import get_reranker, PassthroughReranker


@pytest.mark.asyncio
async def test_cross_encoder_reranking_accuracy():
    reranker = CrossEncoderReranker()
    query = "emergency medical leave policy"

    candidates = [
        RetrievedCandidate(
            chunk_id="c1",
            document_id="d1",
            filename="general_info.txt",
            text="The company offers annual performance bonuses and salary reviews in December.",
            initial_rank=1,
            dense_score=0.72,
        ),
        RetrievedCandidate(
            chunk_id="c2",
            document_id="d2",
            filename="leave_policy.txt",
            text="Employees are entitled to up to 15 business days of paid emergency medical leave per calendar year.",
            initial_rank=2,
            dense_score=0.71,
        )
    ]

    # After reranking, chunk c2 with exact phrase match should be ranked #1
    reranked = await reranker.rerank(query, candidates, top_k=2)
    assert len(reranked) == 2
    assert reranked[0].chunk_id == "c2"
    assert reranked[0].reranked_rank == 1
    assert reranked[0].rerank_score is not None
    assert reranked[0].rerank_score > reranked[1].rerank_score


@pytest.mark.asyncio
async def test_passthrough_reranker():
    reranker = get_reranker(enabled=False)
    assert isinstance(reranker, PassthroughReranker)

    candidates = [
        RetrievedCandidate(
            chunk_id="c1",
            document_id="d1",
            filename="doc1.txt",
            text="Context 1",
            initial_rank=1,
        )
    ]
    reranked = await reranker.rerank("query", candidates)
    assert reranked[0].chunk_id == "c1"
    assert reranked[0].rerank_score is None
