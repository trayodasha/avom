from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.evaluation import EvaluationRun, EvaluationResultItem
from app.schemas.evaluation import (
    EvaluationRunCreate,
    EvaluationRunResponse,
    EvaluationRunDetailResponse,
)
from app.services.evaluation.evaluator_service import EvaluatorService

router = APIRouter()


@router.post("/run", response_model=EvaluationRunDetailResponse, status_code=status.HTTP_201_CREATED)
async def trigger_evaluation_run(
    payload: EvaluationRunCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = EvaluatorService(db)
    run = await service.create_run(
        project_id=payload.project_id,
        dataset_id=payload.dataset_id,
        name=payload.name,
        configuration=payload.configuration
    )
    completed_run = await service.execute_run(run.id)

    # Fetch with items
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == completed_run.id)
    )
    res = await db.execute(stmt)
    full_run = res.scalar_one()
    return full_run


@router.get("", response_model=List[EvaluationRunResponse])
async def list_evaluation_runs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = (
        select(EvaluationRun)
        .where(EvaluationRun.project_id == project_id)
        .order_by(desc(EvaluationRun.created_at))
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{run_id}", response_model=EvaluationRunDetailResponse)
async def get_evaluation_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == run_id)
    )
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation run not found")
    return run
