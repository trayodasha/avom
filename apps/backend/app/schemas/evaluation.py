from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.evaluation import EvaluationStatus
from app.schemas.query import RAGConfiguration


class EvaluationRunCreate(BaseModel):
    project_id: str = Field(..., description="Project workspace ID")
    dataset_id: str = Field(..., description="Evaluation dataset ID")
    name: Optional[str] = Field(default=None, description="Descriptive run name")
    configuration: Optional[RAGConfiguration] = Field(default_factory=RAGConfiguration)


class EvaluationResultItemResponse(BaseModel):
    id: str
    run_id: str
    example_id: str
    query: str
    ground_truth: str
    generated_answer: str
    retrieved_chunk_ids: List[str] = []
    scores: Dict[str, float] = {}
    latency_ms: float
    tokens: Dict[str, int] = {}
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunResponse(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    name: str
    status: EvaluationStatus
    configuration_snapshot: Dict[str, Any]
    aggregate_metrics: Dict[str, float]
    total_examples: int
    processed_examples: int
    duration_ms: float
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EvaluationRunDetailResponse(EvaluationRunResponse):
    results: List[EvaluationResultItemResponse] = []


class ExperimentComparisonResponse(BaseModel):
    runs: List[EvaluationRunResponse]
    metric_keys: List[str]
    matrix: Dict[str, Dict[str, Optional[float]]]  # run_id -> {metric_name: score}
    deltas: Dict[str, Dict[str, Optional[float]]]  # run_id -> {metric_name: delta_vs_baseline}
