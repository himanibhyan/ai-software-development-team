from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.logging import get_logger
from app.db.repositories.artifact_repo import ArtifactRepository
from app.db.repositories.project_repo import ProjectRepository
from app.models.domain.enums import ProjectStatus
from app.services.storage_service import storage_service

logger = get_logger(__name__)


class PersistService:
    """Orchestrates persistence of pipeline state to both DB and disk.

    On every agent completion this service:
    1. Saves the artifact to PostgreSQL via the repository layer
    2. Saves a checkpoint to disk for disaster recovery
    3. Updates the project status in the database
    4. Logs the execution record
    5. Generates a manifest describing current project state
    """

    async def persist_agent_output(
        self,
        _project_repo: ProjectRepository,
        artifact_repo: ArtifactRepository,
        project_id: UUID,
        agent_type: str,
        artifact_type: str,
        content: dict[str, Any],
        state: dict[str, Any],
        revision: int = 1,
    ) -> None:
        """Persist a single agent's output to DB + disk checkpoint."""
        # — DB: save artifact —
        await artifact_repo.create(
            project_id=project_id,
            agent_type=agent_type,
            artifact_type=artifact_type,
            content=content,
            revision=revision,
        )

        # — Disk: incremental checkpoint —
        storage_service.save_checkpoint(
            project_id=str(project_id),
            state=state,
            description=f"Agent {agent_type} completed (rev {revision})",
        )

        logger.info(
            "agent_output_persisted",
            project_id=str(project_id),
            agent=agent_type,
            revision=revision,
        )

    async def persist_generated_code(
        self,
        project_id: UUID,
        files: list[dict[str, str]],
        revision: int = 1,
    ) -> None:
        """Persist generated source code files to disk."""
        storage_service.save_generated_code(
            project_id=str(project_id),
            files=files,
            revision=revision,
        )

    async def finalize_project(
        self,
        project_repo: ProjectRepository,
        project_id: UUID,
        state: dict[str, Any],
    ) -> None:
        """Finalize a completed project: update status, create backup, save final manifest."""
        status = (
            ProjectStatus.COMPLETED
            if state.get("errors") is None or len(state["errors"]) == 0
            else ProjectStatus.FAILED
        )

        await project_repo.update(
            project_id,
            status=status,
            completed_at=datetime.now(UTC),
        )

        # — Final checkpoint —
        storage_service.save_checkpoint(
            project_id=str(project_id),
            state=state,
            description=f"Project finalized: {status.value}",
        )

        # — Backup —
        storage_service.create_backup(name=f"project_{project_id}")

        # — Manifest —
        manifest = {
            "project_id": str(project_id),
            "status": status.value,
            "revision": state.get("revision", 0),
            "completed_at": datetime.now(UTC).isoformat(),
            "artifacts": {
                k: v is not None
                for k, v in state.items()
                if k in ("requirements", "architecture", "source_code", "test_suite", "documentation", "review_report")
            },
            "token_summary": self._sum_tokens(state.get("token_usage", [])),
        }
        storage_service.save_manifest(str(project_id), manifest)

        logger.info(
            "project_finalized",
            project_id=str(project_id),
            status=status.value,
        )

    def _sum_tokens(self, token_usage: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "prompt_tokens": sum(t.get("prompt_tokens", 0) for t in token_usage),
            "completion_tokens": sum(t.get("completion_tokens", 0) for t in token_usage),
            "total_tokens": sum(t.get("total_tokens", 0) for t in token_usage),
        }


persist_service = PersistService()
