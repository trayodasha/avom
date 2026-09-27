from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.repositories.project_repo import ProjectRepository


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProjectRepository(db)

    def _verify_access(self, project: Project, user: User) -> None:
        if project.user_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to access this project workspace."
            )

    async def list_projects(self, user: User, skip: int = 0, limit: int = 100) -> List[ProjectResponse]:
        if user.role == UserRole.ADMIN:
            projects = await self.repo.list_all(skip=skip, limit=limit)
        else:
            projects = await self.repo.list_by_user(user.id, skip=skip, limit=limit)
        return [ProjectResponse.model_validate(p) for p in projects]

    async def get_project(self, project_id: str, user: User) -> ProjectResponse:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        self._verify_access(project, user)
        return ProjectResponse.model_validate(project)

    async def create_project(self, project_in: ProjectCreate, user: User) -> ProjectResponse:
        project = await self.repo.create(project_in, user_id=user.id)
        return ProjectResponse.model_validate(project)

    async def update_project(
        self, project_id: str, project_in: ProjectUpdate, user: User
    ) -> ProjectResponse:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        self._verify_access(project, user)
        updated = await self.repo.update(project, project_in)
        return ProjectResponse.model_validate(updated)

    async def delete_project(self, project_id: str, user: User) -> None:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found."
            )
        self._verify_access(project, user)
        await self.repo.delete(project)
