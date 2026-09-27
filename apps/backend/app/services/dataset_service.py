import logging
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.dataset import EvaluationDataset, EvaluationExample
from app.models.user import User, UserRole
from app.repositories.project_repo import ProjectRepository
from app.schemas.dataset import EvaluationDatasetCreate, EvaluationExampleCreate

logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.proj_repo = ProjectRepository(db)

    async def create_dataset(self, data: EvaluationDatasetCreate, user: User) -> EvaluationDataset:
        project = await self.proj_repo.get_by_id(data.project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        dataset = EvaluationDataset(
            project_id=data.project_id,
            name=data.name,
            description=data.description,
            example_count=0
        )
        self.db.add(dataset)
        await self.db.commit()
        await self.db.refresh(dataset)
        return dataset

    async def list_datasets(self, project_id: str, user: User) -> List[EvaluationDataset]:
        project = await self.proj_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        if project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        stmt = select(EvaluationDataset).where(EvaluationDataset.project_id == project_id).order_by(desc(EvaluationDataset.created_at))
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_dataset(self, dataset_id: str, user: User) -> EvaluationDataset:
        stmt = select(EvaluationDataset).where(EvaluationDataset.id == dataset_id)
        res = await self.db.execute(stmt)
        dataset = res.scalar_one_or_none()
        if not dataset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
        return dataset

    async def add_examples(self, dataset_id: str, examples: List[EvaluationExampleCreate], user: User) -> List[EvaluationExample]:
        dataset = await self.get_dataset(dataset_id, user)
        created_examples = []
        for ex in examples:
            item = EvaluationExample(
                dataset_id=dataset.id,
                project_id=dataset.project_id,
                query=ex.query,
                ground_truth=ex.ground_truth,
                ground_truth_chunk_ids=ex.ground_truth_chunk_ids,
                ground_truth_context=ex.ground_truth_context,
                metadata_json=ex.metadata_json
            )
            self.db.add(item)
            created_examples.append(item)

        dataset.example_count += len(examples)
        await self.db.commit()
        for item in created_examples:
            await self.db.refresh(item)
        return created_examples

    async def get_examples(self, dataset_id: str, user: User) -> List[EvaluationExample]:
        await self.get_dataset(dataset_id, user)
        stmt = select(EvaluationExample).where(EvaluationExample.dataset_id == dataset_id).order_by(EvaluationExample.created_at)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def delete_dataset(self, dataset_id: str, user: User) -> None:
        dataset = await self.get_dataset(dataset_id, user)
        await self.db.delete(dataset)
        await self.db.commit()
