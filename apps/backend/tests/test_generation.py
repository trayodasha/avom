import pytest
from httpx import AsyncClient
from app.services.generation.prompts import DEFAULT_RAG_SYSTEM_PROMPT, build_rag_prompt
from app.services.generation.citation_extractor import CitationExtractor
from app.services.retrieval.retriever import RetrievedCandidate
from app.services.generation.providers.local_provider import LocalDeterministicProvider
from tests.test_ingestion import create_user_project


def test_prompt_builder():
    assert "precision rag synthesis" in DEFAULT_RAG_SYSTEM_PROMPT.lower()

    candidates = [
        RetrievedCandidate(
            chunk_id="c1",
            document_id="d1",
            filename="overview.pdf",
            text="Antigravity is an AI development platform.",
            dense_score=0.9,
            sparse_score=0.5,
            rrf_score=0.8,
        ),
        RetrievedCandidate(
            chunk_id="c2",
            document_id="d2",
            filename="search.pdf",
            text="BM25 is a probabilistic retrieval model.",
            dense_score=0.7,
            sparse_score=0.9,
            rrf_score=0.85,
        ),
    ]
    user_prompt = build_rag_prompt("What is Antigravity?", candidates)
    assert "[1] (Document: overview.pdf)" in user_prompt
    assert "Antigravity is an AI development platform." in user_prompt
    assert "What is Antigravity?" in user_prompt


def test_citation_extractor():
    candidates = [
        RetrievedCandidate(
            chunk_id="c1",
            document_id="d1",
            filename="overview.pdf",
            text="Antigravity provides intelligent agent workflows.",
        ),
        RetrievedCandidate(
            chunk_id="c2",
            document_id="d2",
            filename="search.pdf",
            text="BM25 is used for sparse retrieval.",
        ),
    ]
    answer_text = "Antigravity accelerates development [1], while BM25 handles sparse search [2]."
    citations = CitationExtractor.extract_citations(answer_text, candidates)
    assert len(citations) == 2
    assert citations[0]["chunk_id"] == "c1"
    assert citations[0]["filename"] == "overview.pdf"
    assert citations[1]["chunk_id"] == "c2"


@pytest.mark.asyncio
async def test_deterministic_llm_generation():
    provider = LocalDeterministicProvider()
    response = await provider.generate(
        system_prompt="You are a helpful assistant.",
        prompt="[1] AVOM is a RAG evaluation engine.\n\nUser Query: What is AVOM?",
    )
    assert response.content is not None
    assert len(response.content) > 0
    assert response.input_tokens > 0


@pytest.mark.asyncio
async def test_query_pipeline_e2e(client: AsyncClient):
    token, project_id = await create_user_project(client, "query_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload a test document with rich content
    content = (
        "PostgreSQL is an open-source relational database management system emphasizing extensibility and SQL compliance. "
        "Qdrant is a vector similarity search engine and vector database written in Rust. "
        "AVOM utilizes both PostgreSQL for metadata storage and Qdrant for dense high-dimensional vector search. "
        "Hybrid search combines dense vectors with BM25 keyword matching via Reciprocal Rank Fusion."
    )
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "project_id": project_id,
            "chunking_strategy": "fixed",
            "chunk_size": 150,
            "chunk_overlap": 20,
        },
        files={"file": ("architecture.txt", content.encode("utf-8"), "text/plain")},
    )
    assert upload_resp.status_code == 201

    # 2. Query with Hybrid Retrieval + Reranking
    query_payload = {
        "project_id": project_id,
        "query": "What database does AVOM use for vector search?",
        "configuration": {
            "retrieval_type": "hybrid",
            "top_k": 5,
            "reranking": True,
            "rerank_top_k": 3,
            "final_context_k": 2,
            "llm_model": "local-deterministic",
        }
    }

    resp = await client.post("/api/v1/query", json=query_payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "retrieved_chunks" in data
    assert len(data["retrieved_chunks"]) > 0
    assert "trace_id" in data
    assert "latency_ms" in data

    # Check chunk schema
    top_chunk = data["retrieved_chunks"][0]
    assert "text" in top_chunk
    assert "dense_score" in top_chunk
    assert "sparse_score" in top_chunk
    assert "rrf_score" in top_chunk
    assert "rerank_score" in top_chunk
