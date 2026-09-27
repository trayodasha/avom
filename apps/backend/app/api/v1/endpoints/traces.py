from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.trace import TraceRecordResponse
from app.services.tracing_service import TracingService

router = APIRouter()


@router.get("", response_model=List[TraceRecordResponse])
async def list_traces(
    project_id: str = Query(..., description="Project workspace ID"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = TracingService(db)
    return await service.list_traces(project_id=project_id, limit=limit, skip=skip)


@router.get("/{trace_id}", response_model=TraceRecordResponse)
async def get_trace_detail(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = TracingService(db)
    trace = await service.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace record not found")
    return trace
