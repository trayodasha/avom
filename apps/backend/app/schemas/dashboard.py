from typing import List, Dict, Any
from pydantic import BaseModel


class SystemMetricsSummary(BaseModel):
    total_projects: int
    total_documents: int
    total_chunks: int
    total_evaluations: int
    total_traces: int
    avg_latency_ms: float
    avg_faithfulness: float
    avg_recall: float
    recent_activity: List[Dict[str, Any]] = []
