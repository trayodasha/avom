from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class EvaluationExampleBase(BaseModel):
    query: str = Field(..., min_length=1, description="Question or prompt")
    ground_truth: str = Field(..., min_length=1, description="Reference ground truth answer")
    ground_truth_chunk_ids: List[str] = Field(default_factory=list, description="IDs of ground truth chunks")
    ground_truth_context: Optional[str] = Field(default=None, description="Reference passage context")
    metadata_json: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata tags")


class EvaluationExampleCreate(EvaluationExampleBase):
    pass


class EvaluationExampleResponse(EvaluationExampleBase):
    id: str
    dataset_id: str
    project_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationDatasetCreate(BaseModel):
    project_id: str = Field(..., description="Project workspace ID")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class EvaluationDatasetResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    example_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvaluationDatasetDetailResponse(EvaluationDatasetResponse):
    examples: List[EvaluationExampleResponse] = []


class BulkExamplesUploadRequest(BaseModel):
    examples: List[EvaluationExampleCreate]
