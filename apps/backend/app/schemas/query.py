from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class RAGConfiguration(BaseModel):
    embedding_model: str = Field(default="bge-small-en-v1.5", description="Model for embedding generation")
    retrieval_type: str = Field(default="hybrid", description="dense, sparse, or hybrid")
    top_k: int = Field(default=20, ge=1, le=100, description="Initial candidates retrieved")
    dense_weight: float = Field(default=1.0, ge=0.0, le=5.0, description="Dense score weight for RRF")
    sparse_weight: float = Field(default=1.0, ge=0.0, le=5.0, description="Sparse BM25 weight for RRF")
    reranking: bool = Field(default=True, description="Enable cross-encoder reranking")
    reranker_model: str = Field(default="BAAI/bge-reranker-base", description="Cross-encoder model identifier")
    rerank_top_k: int = Field(default=8, ge=1, le=50, description="Candidates sent to reranker")
    final_context_k: int = Field(default=5, ge=1, le=20, description="Final context chunks passed to LLM")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model used for synthesis")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Generation temperature")


class QueryRequest(BaseModel):
    project_id: str = Field(..., description="Project workspace UUID")
    query: str = Field(..., min_length=1, description="User search or prompt query")
    configuration: Optional[RAGConfiguration] = Field(default_factory=RAGConfiguration)


class ScoredChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    text: str
    dense_score: float
    sparse_score: float
    rrf_score: float
    rerank_score: Optional[float] = None
    initial_rank: int
    reranked_rank: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class CitationResponse(BaseModel):
    citation_id: int
    chunk_id: str
    document_id: str
    filename: str
    dense_score: float
    sparse_score: float
    rerank_score: Optional[float] = None
    preview: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    answer: str
    sources: List[CitationResponse] = []
    retrieved_chunks: List[ScoredChunkResponse] = []
    scores: Dict[str, Any] = Field(default_factory=dict)
    trace_id: str
    latency_ms: float
    tokens: Dict[str, int] = Field(default_factory=dict)
