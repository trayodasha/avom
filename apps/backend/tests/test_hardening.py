import pytest
from httpx import AsyncClient
from app.services.evaluation.failure_classifier import FailureClassifier, FailureCategory


def test_failure_classifier_zero_chunks():
    diag = FailureClassifier.diagnose(
        scores={"faithfulness": 0.0},
        retrieved_chunk_count=0,
        has_citations=False,
    )
    assert diag["category"] == FailureCategory.NO_RELEVANT_CONTEXT.value
    assert "0 chunks" in diag["reason"]


def test_failure_classifier_low_recall():
    diag = FailureClassifier.diagnose(
        scores={"recall@k": 0.1, "faithfulness": 0.9},
        retrieved_chunk_count=5,
        has_citations=True,
    )
    assert diag["category"] == FailureCategory.BAD_RETRIEVAL.value


def test_failure_classifier_hallucination():
    diag = FailureClassifier.diagnose(
        scores={"recall@k": 0.9, "faithfulness": 0.4},
        retrieved_chunk_count=5,
        has_citations=True,
    )
    assert diag["category"] == FailureCategory.HALLUCINATION.value


def test_failure_classifier_success():
    diag = FailureClassifier.diagnose(
        scores={"recall@k": 0.95, "faithfulness": 0.95, "answer_relevance": 0.92},
        retrieved_chunk_count=5,
        has_citations=True,
    )
    assert diag["category"] == FailureCategory.SUCCESS.value


@pytest.mark.asyncio
async def test_security_headers_and_request_id(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200

    # Verify OWASP Security Headers
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert "strict-origin" in res.headers.get("Referrer-Policy", "")

    # Verify Correlation ID and Timing
    assert "X-Request-ID" in res.headers
    assert "X-Response-Time" in res.headers


@pytest.mark.asyncio
async def test_custom_request_id_preserved(client: AsyncClient):
    custom_id = "custom-req-trace-xyz-123"
    res = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_id
