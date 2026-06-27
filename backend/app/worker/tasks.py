from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

import redis as sync_redis
from sqlalchemy import create_engine, text

from app.agents.registry import init_registry
from app.config import settings
from app.core.logging import get_logger
from app.graph.pipeline import get_pipeline
from app.graph.state import create_initial_state, state_summary
from app.services.llm_service import llm_service
from app.worker.celery_app import celery_app

logger = get_logger(__name__)

# Sync engine for Celery worker DB updates — avoids event-loop conflicts
# that arise when using the async engine (from session.py) across
# asyncio.run() boundaries in ForkPoolWorker processes.
_SYNC_DB_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
_sync_engine = create_engine(_SYNC_DB_URL, pool_pre_ping=True)

# Sync Redis client for event publishing in the Celery worker.
_sync_redis = sync_redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5)  # type: ignore[no-untyped-call]


def _sync_update_project_status(
    project_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Update the project's status and completion timestamp in the database.

    Uses a synchronous SQLAlchemy engine to avoid event-loop conflicts
    in the Celery ForkPoolWorker process.
    """
    now = datetime.now(UTC)
    try:
        with _sync_engine.begin() as conn:
            conn.execute(
                text(
                    """UPDATE projects
                       SET status = :status,
                           completed_at = :completed_at,
                           error_message = :error_message,
                           updated_at = :updated_at
                       WHERE id = :id"""
                ),
                {
                    "status": status,
                    "completed_at": now,
                    "error_message": error_message,
                    "updated_at": now,
                    "id": project_id,
                },
            )
        logger.info(
            "project_status_updated",
            project_id=project_id,
            status=status,
        )
    except Exception as e:
        logger.error(
            "project_status_update_failed",
            project_id=project_id,
            status=status,
            error=str(e),
        )


def _sync_publish_event(project_id: str, event_type: str, data: dict) -> None:
    """Publish an event to Redis pub/sub using a sync Redis client.

    Celery workers are synchronous processes. Using ``redis.asyncio``
    in this context causes "Event loop is closed" errors because
    ``asyncio.run()`` creates and destroys an event loop per invocation,
    stranding async resources.
    """
    channel = f"project:{project_id}:events"
    message = json.dumps({"type": event_type, "project_id": project_id, "data": data})
    try:
        _sync_redis.publish(channel, message)
    except Exception as exc:
        logger.debug(
            "redis_publish_failed",
            channel=channel,
            event_type=event_type,
            error=str(exc),
        )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_generation_pipeline(
    self,
    idea: str,
    project_id: str,
    constraints: dict | None = None,
) -> dict:
    """Execute the full agent generation pipeline in the background.

    The pipeline runs via ``asyncio.run()`` (required for LangGraph's
    async nodes). All database updates and event publishing use
    **synchronous** clients to avoid event-loop conflicts in the
    Celery ForkPoolWorker process.

    The project status is always persisted to the database, both on
    success and on failure (after the last retry), so the API never
    shows a stuck ``pending`` status.

    Retry Strategy:
    - 3 retries with 30s exponential backoff
    - Retries on transient failures (network, rate limit)
    - The project row is only marked ``failed`` on the final retry
    """

    async def _run_pipeline() -> dict:
        """Run the LangGraph pipeline in a single async context.

        Only the pipeline execution lives here.  DB and Redis I/O are
        handled synchronously by the outer function.
        """
        # Initialize registry if needed (fallback for solo pool / direct dispatch)
        if not hasattr(run_generation_pipeline, "_registry_initialized"):
            if llm_service.is_available:
                await llm_service.initialize()
                init_registry(llm_service)
            run_generation_pipeline._registry_initialized = True

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

        pipeline = get_pipeline()
        final_state = await pipeline.ainvoke(
            state,
            config={"configurable": {"thread_id": project_id}},
        )

        return final_state

    logger.info(
        "pipeline_task_started",
        project_id=project_id,
        task_id=self.request.id,
    )

    _sync_publish_event(project_id, "pipeline_started", {})

    final_state: dict | None = None

    try:
        final_state = asyncio.run(_run_pipeline())
        status = final_state.get("status", "failed")
        summary = state_summary(final_state)  # type: ignore[arg-type]

        _sync_publish_event(project_id, "pipeline_completed", {"status": status, "summary": summary})

        _sync_update_project_status(project_id, status)

        logger.info("pipeline_task_completed", project_id=project_id, summary=summary)

        return {
            "project_id": project_id,
            "status": status,
            "revision": final_state.get("revision"),
            "has_requirements": final_state.get("requirements") is not None,
            "has_architecture": final_state.get("architecture") is not None,
            "has_source_code": final_state.get("source_code") is not None,
            "has_tests": final_state.get("test_suite") is not None,
            "has_documentation": final_state.get("documentation") is not None,
            "has_review": final_state.get("review_report") is not None,
            "error_count": len(final_state.get("errors", [])),
            "warning_count": len(final_state.get("warnings", [])),
        }

    except Exception as exc:
        logger.error(
            "pipeline_task_failed",
            project_id=project_id,
            error=str(exc),
            task_id=self.request.id,
        )

        # Only persist failure to DB on the last retry
        if self.request.retries >= self.max_retries:
            _sync_update_project_status(project_id, "failed", error_message=str(exc))

        _sync_publish_event(project_id, "pipeline_error", {"error": str(exc)})

        raise self.retry(exc=exc) from exc
