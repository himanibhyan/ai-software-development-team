from __future__ import annotations

from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventPublisher:
    """Publish events during agent execution for real-time streaming.

    In production, this publishes to Redis pub/sub channels.
    The WebSocket handler subscribes to these channels to push
    updates to connected clients.
    """

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        self.channel = f"project:{project_id}:events"

    async def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to the project's event channel."""
        message = {
            "type": event_type,
            "project_id": self.project_id,
            "data": data,
        }
        # TODO: Publish to Redis pub/sub
        logger.debug(
            "event_published",
            channel=self.channel,
            event_type=event_type,
        )

    async def agent_started(self, agent_type: str) -> None:
        await self.publish("agent_started", {"agent_type": agent_type})

    async def agent_completed(
        self, agent_type: str, duration_ms: int, token_usage: dict[str, int]
    ) -> None:
        await self.publish("agent_completed", {
            "agent_type": agent_type,
            "duration_ms": duration_ms,
            "token_usage": token_usage,
        })

    async def agent_error(self, agent_type: str, error: str) -> None:
        await self.publish("agent_error", {"agent_type": agent_type, "error": error})

    async def artifact_generated(self, artifact_type: str, preview: str) -> None:
        await self.publish("artifact_generated", {
            "artifact_type": artifact_type,
            "preview": preview[:200],
        })
