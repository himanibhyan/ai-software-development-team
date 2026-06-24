from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.exceptions import AgentException
from app.core.logging import get_logger
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.services.llm_service import LLMService

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline.

    Each agent:
    1. Reads relevant context from shared state
    2. Calls the LLM with a domain-specific system prompt
    3. Validates and parses the structured output
    4. Returns state updates to be merged by LangGraph
    """

    # Maps agent_type → shared state field name
    STATE_FIELD_MAP: dict[AgentType, str] = {
        AgentType.REQUIREMENTS: "requirements",
        AgentType.ARCHITECT: "architecture",
        AgentType.DEVELOPER: "source_code",
        AgentType.CODE_REVIEW: "review_report",
        AgentType.TESTER: "test_suite",
        AgentType.DOCUMENTATION: "documentation",
    }

    def __init__(self, llm_service: LLMService) -> None:
        self.llm = llm_service
        self.max_retries: int = 2

    @property
    @abstractmethod
    def agent_type(self) -> AgentType: ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    @property
    @abstractmethod
    def output_model(self) -> type[BaseModel]: ...

    def build_user_prompt(self, state: GraphState) -> str:
        """Build the user prompt from current state context."""
        context_parts = [f"## Software Idea\n{state['idea']}"]
        if state.get("constraints"):
            context_parts.append(f"## Constraints\n{state['constraints']}")
        return "\n\n".join(context_parts)

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Execute the agent's task and return state updates.

        Args:
            state: Current pipeline state

        Returns:
            Dict of state updates to merge

        Raises:
            AgentException: If processing fails after retries
        """
        logger.info(
            "agent_started",
            agent_type=self.agent_type.value,
            project_id=state["project_id"],
        )

        for attempt in range(self.max_retries + 1):
            try:
                user_prompt = self.build_user_prompt(state)
                parsed, token_usage = await self.llm.generate(
                    system_prompt=self.system_prompt,
                    user_prompt=user_prompt,
                    response_model=self.output_model,
                )

                validated = self._validate_output(parsed)
                updates = self._build_state_updates(state, validated, token_usage)

                logger.info(
                    "agent_completed",
                    agent_type=self.agent_type.value,
                    project_id=state["project_id"],
                    attempt=attempt + 1,
                    token_usage=token_usage,
                )

                return updates

            except (ValidationError, ValueError) as e:
                logger.warning(
                    "agent_validation_error",
                    agent_type=self.agent_type.value,
                    attempt=attempt + 1,
                    error=str(e),
                    project_id=state["project_id"],
                )
                if attempt < self.max_retries:
                    continue
                raise AgentException(
                    agent_type=self.agent_type.value,
                    message=f"Validation failed after {self.max_retries + 1} attempts: {e}",
                ) from e

            except Exception as e:
                logger.error(
                    "agent_execution_error",
                    agent_type=self.agent_type.value,
                    attempt=attempt + 1,
                    error=str(e),
                    project_id=state["project_id"],
                )
                if attempt < self.max_retries:
                    continue
                raise AgentException(
                    agent_type=self.agent_type.value,
                    message=f"Execution failed after {self.max_retries + 1} attempts: {e}",
                ) from e

    def _validate_output(self, output: BaseModel) -> BaseModel:
        """Validate the agent's output. Override for domain-specific checks."""
        return output

    def _state_field(self) -> str:
        """Get the shared state field name for this agent's output."""
        return self.STATE_FIELD_MAP.get(self.agent_type, self.agent_type.value)

    def _build_state_updates(
        self,
        state: GraphState,
        output: BaseModel,
        token_usage: dict[str, int],
    ) -> dict[str, Any]:
        """Build state updates from validated output.

        Includes:
        - The generated artifact (serialized to dict)
        - Current agent type for tracking
        - Incremented revision number
        - Token usage for cost tracking
        """
        field = self._state_field()
        updates: dict[str, Any] = {
            field: output.model_dump(),
            "current_agent": self.agent_type.value,
            "revision": state["revision"] + 1,
        }
        if token_usage:
            updates["token_usage"] = [
                {
                    "agent": self.agent_type.value,
                    **token_usage,
                }
            ]
        return updates
