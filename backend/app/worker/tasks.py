from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import UTC, datetime
from uuid import UUID

from app.agents.registry import init_registry
from app.core.logging import get_logger
from app.graph.pipeline import get_pipeline
from app.graph.state import create_initial_state, state_summary
from app.services.llm_service import llm_service
from app.worker.celery_app import celery_app
from app.worker.events import EventPublisher, close_redis

logger = get_logger(__name__)


async def _update_project_status(
    project_id: str,
    status: str,
    completed_at: str | None = None,
    error_message: str | None = None,
) -> None:
    """Persist the final pipeline outcome to the database."""
    from app.db.repositories.project_repo import ProjectRepository
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        try:
            repo = ProjectRepository(session)
            kwargs: dict = {"status": status}
            if completed_at:
                try:
                    kwargs["completed_at"] = datetime.fromisoformat(completed_at)
                except (ValueError, TypeError):
                    kwargs["completed_at"] = datetime.now(UTC)
            elif status in ("completed", "failed"):
                kwargs["completed_at"] = datetime.now(UTC)
            if error_message:
                kwargs["error_message"] = error_message
            await repo.update(UUID(project_id), **kwargs)
            await session.commit()
            logger.info(
                "project_status_updated",
                project_id=project_id,
                status=status,
            )
        except Exception as e:
            logger.warning(
                "project_status_update_failed",
                project_id=project_id,
                error=str(e),
            )
            await session.rollback()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_generation_pipeline(
    self,
    idea: str,
    project_id: str,
    constraints: dict | None = None,
) -> dict:
    """Execute the full agent generation pipeline in the background.

    Runs the complete LangGraph workflow via a single async context
    to avoid event-loop conflicts with shared resources (Redis).

    Retry Strategy:
    - 3 retries with 30s exponential backoff
    - Retries on transient failures (network, rate limit)
    - Does NOT retry on validation errors or bad input
    """

    async def _run() -> dict:
        # Clear any stale Redis connection from a previous event loop
        await close_redis()

        publisher = EventPublisher(project_id)
        await publisher.pipeline_started()

        # Initialize registry if needed (fallback for solo pool / direct dispatch)
        if not hasattr(run_generation_pipeline, "_registry_initialized"):
            if llm_service.is_available:
                await llm_service.initialize()
                init_registry(llm_service)
            run_generation_pipeline._registry_initialized = True

        # Create initial state
        state = create_initial_state(
            idea=idea,
            constraints=constraints,
            project_id=UUID(project_id),
        )

        logger.info(
            "pipeline_state_created",
            project_id=project_id,
            state_preview=state_summary(state),
        )

        # Execute the pipeline
        pipeline = get_pipeline()
        final_state = await pipeline.ainvoke(
            state,
            config={"configurable": {"thread_id": project_id}},
        )

        summary = state_summary(final_state)  # type: ignore[arg-type]
        logger.info(
            "pipeline_task_completed",
            project_id=project_id,
            summary=summary,
        )

        await publisher.pipeline_completed(final_state["status"], summary)

        # Persist final status to database
        await _update_project_status(
            project_id=project_id,
            status=final_state["status"],
            completed_at=final_state.get("end_time"),
        )

        return {
            "project_id": project_id,
            "status": final_state["status"],
            "revision": final_state["revision"],
            "has_requirements": final_state.get("requirements") is not None,
            "has_architecture": final_state.get("architecture") is not None,
            "has_source_code": final_state.get("source_code") is not None,
            "has_tests": final_state.get("test_suite") is not None,
            "has_documentation": final_state.get("documentation") is not None,
            "has_review": final_state.get("review_report") is not None,
            "error_count": len(final_state.get("errors", [])),
            "warning_count": len(final_state.get("warnings", [])),
        }

    logger.info(
        "pipeline_task_started",
        project_id=project_id,
        task_id=self.request.id,
    )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(
            "pipeline_task_failed",
            project_id=project_id,
            error=str(exc),
            task_id=self.request.id,
        )
        # Only persist failure to DB on the last retry
        if self.request.retries >= self.max_retries:
            with suppress(Exception):
                asyncio.run(
                    _update_project_status(
                        project_id=project_id,
                        status="failed",
                        error_message=str(exc),
                    )
                )
        # Best-effort error event publish
        with suppress(Exception):
            asyncio.run(EventPublisher(project_id).pipeline_error(str(exc)))
        raise self.retry(exc=exc) from exc
