import pytest
from app.services.retrieval.bm25 import BM25Index
from app.services.retrieval.rrf import ReciprocalRankFusion


def test_bm25_keyword_matching():
    index = BM25Index()
    docs = [
        {"id": "doc1", "text": "Kubernetes cluster container orchestration with Docker and pods."},
        {"id": "doc2", "text": "PostgreSQL relational database schema design and migrations."},
        {"id": "doc3", "text": "Retrieval Augmented Generation with vector embeddings and BM25."},
    ]
    index.index_documents(docs)

    # Search for RAG
    results = index.search("retrieval embeddings", top_k=2)
    assert len(results) > 0
    assert results[0][0] == "doc3"
    assert results[0][1] > 0.0

    # Search for Kubernetes
    k8s_results = index.search("kubernetes pods", top_k=2)
    assert len(k8s_results) > 0
    assert k8s_results[0][0] == "doc1"


def test_reciprocal_rank_fusion():
    rrf = ReciprocalRankFusion(k=60)
    dense_results = [("chunk_a", 0.95), ("chunk_b", 0.88), ("chunk_c", 0.70)]
    sparse_results = [("chunk_b", 12.5), ("chunk_d", 8.2), ("chunk_a", 5.1)]

    # chunk_b is ranked #2 in dense and #1 in sparse -> should get highest fused rank!
    fused = rrf.fuse(
        dense_results=dense_results,
        sparse_results=sparse_results,
        dense_weight=1.0,
        sparse_weight=1.0,
        top_k=4
    )

    assert len(fused) == 4
    assert fused[0]["chunk_id"] == "chunk_b"
    assert fused[0]["initial_rank"] == 1
    assert fused[0]["dense_score"] == 0.88
    assert fused[0]["sparse_score"] == 12.5
    assert fused[0]["dense_rank"] == 2
    assert fused[0]["sparse_rank"] == 1
