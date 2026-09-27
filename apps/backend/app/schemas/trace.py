from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class TraceSpan(BaseModel):
    name: str = Field(..., description="Span name, e.g. query_embedding, dense_retrieval, bm25_search, cross_encoder, llm_generation")
    start_time_ms: float
    end_time_ms: float
    duration_ms: float
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TraceRecordResponse(BaseModel):
    id: str
    project_id: str
    user_id: Optional[str] = None
    query: str
    answer: Optional[str] = None
    status: str
    total_latency_ms: float
    input_tokens: int
    output_tokens: int
    configuration_json: Dict[str, Any] = {}
    spans_json: List[Dict[str, Any]] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
