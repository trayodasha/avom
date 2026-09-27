from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dataset import (
    EvaluationDatasetCreate,
    EvaluationDatasetResponse,
    EvaluationExampleCreate,
    EvaluationExampleResponse,
    BulkExamplesUploadRequest
)
from app.services.dataset_service import DatasetService

router = APIRouter()


@router.post("", response_model=EvaluationDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    payload: EvaluationDatasetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = DatasetService(db)
    return await service.create_dataset(payload, user)


@router.get("", response_model=List[EvaluationDatasetResponse])
async def list_datasets(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = DatasetService(db)
    return await service.list_datasets(project_id, user)


@router.get("/{dataset_id}", response_model=EvaluationDatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = DatasetService(db)
    return await service.get_dataset(dataset_id, user)


@router.post("/{dataset_id}/examples", response_model=List[EvaluationExampleResponse], status_code=status.HTTP_201_CREATED)
async def add_dataset_examples(
    dataset_id: str,
    payload: BulkExamplesUploadRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = DatasetService(db)
    return await service.add_examples(dataset_id, payload.examples, user)


@router.get("/{dataset_id}/examples", response_model=List[EvaluationExampleResponse])
async def list_dataset_examples(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = DatasetService(db)
    return await service.get_examples(dataset_id, user)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = DatasetService(db)
    await service.delete_dataset(dataset_id, user)
