from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.evaluation import EvaluationRun
from app.schemas.evaluation import ExperimentComparisonResponse, EvaluationRunResponse

router = APIRouter()


@router.get("/compare", response_model=ExperimentComparisonResponse)
async def compare_experiments(
    run_ids: List[str] = Query(..., description="List of evaluation run IDs to compare"),
    baseline_id: Optional[str] = Query(None, description="Optional baseline run ID for deltas calculation"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not run_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one run_id must be provided")

    stmt = select(EvaluationRun).where(EvaluationRun.id.in_(run_ids))
    res = await db.execute(stmt)
    runs = list(res.scalars().all())

    if not runs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching evaluation runs found")

    metric_keys = [
        "recall@k",
        "precision@k",
        "mrr",
        "hit_rate@k",
        "ndcg@k",
        "faithfulness",
        "answer_relevance",
        "context_recall",
        "latency_ms"
    ]

    matrix: Dict[str, Dict[str, Optional[float]]] = {}
    for r in runs:
        matrix[r.id] = {}
        for m in metric_keys:
            val = r.aggregate_metrics.get(m)
            matrix[r.id][m] = float(val) if val is not None else None

    # Determine baseline
    baseline_run_id = baseline_id if baseline_id and baseline_id in matrix else runs[0].id
    baseline_scores = matrix[baseline_run_id]

    deltas: Dict[str, Dict[str, Optional[float]]] = {}
    for r_id, scores in matrix.items():
        deltas[r_id] = {}
        for m in metric_keys:
            current_val = scores.get(m)
            base_val = baseline_scores.get(m)
            if current_val is not None and base_val is not None:
                deltas[r_id][m] = round(current_val - base_val, 4)
            else:
                deltas[r_id][m] = None

    return ExperimentComparisonResponse(
        runs=[EvaluationRunResponse.model_validate(r) for r in runs],
        metric_keys=metric_keys,
        matrix=matrix,
        deltas=deltas
    )
