from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.db.project import ProjectModel


class ProjectRepository(BaseRepository[ProjectModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProjectModel, session)

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 100) -> list[ProjectModel]:
        result = await self.session.execute(
            select(ProjectModel).where(ProjectModel.status == status).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_artifacts(self, project_id: UUID) -> ProjectModel | None:
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(ProjectModel).options(selectinload(ProjectModel.artifacts)).where(ProjectModel.id == project_id)
        )
        return result.scalar_one_or_none()
