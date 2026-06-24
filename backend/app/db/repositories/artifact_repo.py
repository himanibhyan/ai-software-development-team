from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.db.artifact import ArtifactModel


class ArtifactRepository(BaseRepository[ArtifactModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ArtifactModel, session)

    async def get_by_project(self, project_id: UUID, skip: int = 0, limit: int = 100) -> list[ArtifactModel]:
        result = await self.session.execute(
            select(ArtifactModel).where(ArtifactModel.project_id == project_id).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_agent_type(self, project_id: UUID, agent_type: str) -> list[ArtifactModel]:
        result = await self.session.execute(
            select(ArtifactModel).where(
                ArtifactModel.project_id == project_id,
                ArtifactModel.agent_type == agent_type,
            )
        )
        return list(result.scalars().all())

    async def get_latest_revision(self, project_id: UUID, agent_type: str) -> ArtifactModel | None:
        result = await self.session.execute(
            select(ArtifactModel)
            .where(
                ArtifactModel.project_id == project_id,
                ArtifactModel.agent_type == agent_type,
            )
            .order_by(ArtifactModel.revision.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
