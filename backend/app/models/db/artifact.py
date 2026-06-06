from __future__ import annotations

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as UUIDType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.domain.enums import AgentType, ArtifactType

if TYPE_CHECKING:
    from app.models.db.project import ProjectModel


class ArtifactModel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "project_artifacts"

    __table_args__ = (
        UniqueConstraint("project_id", "agent_type", "revision", name="uq_artifact_revision"),
    )

    project_id: Mapped[UUID] = mapped_column(
        UUIDType(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    artifact_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    project: Mapped[ProjectModel] = relationship(back_populates="artifacts")
