from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.domain.enums import ArtifactType
from app.models.domain.project import (
    ArchitectureDoc,
    CodeReviewReport,
    Documentation,
    ProjectTree,
    RequirementsDoc,
    TestSuite,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Artifact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    agent_type: str
    artifact_type: ArtifactType
    content: dict[str, Any]
    markdown: str | None = None
    revision: int = 1
    created_at: datetime = Field(default_factory=_utcnow)

    model_config = {"frozen": True}


class RequirementsArtifact(Artifact):
    artifact_type: ArtifactType = ArtifactType.REQUIREMENTS
    content: RequirementsDoc  # type: ignore[assignment]


class ArchitectureArtifact(Artifact):
    artifact_type: ArtifactType = ArtifactType.ARCHITECTURE
    content: ArchitectureDoc  # type: ignore[assignment]


class SourceCodeArtifact(Artifact):
    artifact_type: ArtifactType = ArtifactType.SOURCE_CODE
    content: ProjectTree  # type: ignore[assignment]


class TestSuiteArtifact(Artifact):
    artifact_type: ArtifactType = ArtifactType.TEST_SUITE
    content: TestSuite  # type: ignore[assignment]


class CodeReviewArtifact(Artifact):
    artifact_type: ArtifactType = ArtifactType.CODE_REVIEW
    content: CodeReviewReport  # type: ignore[assignment]


class DocumentationArtifact(Artifact):
    artifact_type: ArtifactType = ArtifactType.DOCUMENTATION
    content: Documentation  # type: ignore[assignment]
