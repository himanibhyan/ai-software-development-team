from __future__ import annotations

import asyncio
from typing import Any

from celery import Celery, signals

from app.config import settings

celery_app = Celery(
    "ai_dev_team",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker.tasks"],
)


@signals.worker_process_init.connect
def init_worker_process(**_kwargs: Any) -> None:
    """Initialize LLM service and agent registry once per worker process."""
    from app.agents.registry import init_registry
    from app.services.llm_service import llm_service

    asyncio.run(llm_service.initialize())
    if llm_service.is_available:
        init_registry(llm_service)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # 9 minutes soft limit
    worker_max_tasks_per_child=10,
    worker_prefetch_multiplier=1,
)
