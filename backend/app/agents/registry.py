from __future__ import annotations

from typing import Union

from app.agents.architect_agent import ArchitectAgent
from app.agents.base import BaseAgent
from app.agents.code_review_agent import CodeReviewAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.requirements_agent import RequirementsAgent
from app.agents.tester_agent import TesterAgent
from app.models.domain.enums import AgentType
from app.services.llm_service import LLMService


class AgentRegistry:
    """Registry of all available agents in the system.

    Provides lookup and instantiation of agents by type.
    Agents are lazily instantiated and cached.
    """

    def __init__(self, llm_service: LLMService) -> None:
        self._agent_classes: dict[AgentType, type[BaseAgent]] = {
            AgentType.REQUIREMENTS: RequirementsAgent,
            AgentType.ARCHITECT: ArchitectAgent,
            AgentType.DEVELOPER: DeveloperAgent,
            AgentType.CODE_REVIEW: CodeReviewAgent,
            AgentType.TESTER: TesterAgent,
            AgentType.DOCUMENTATION: DocumentationAgent,
        }
        self._instances: dict[AgentType, BaseAgent] = {}
        self._llm = llm_service

    def _resolve_type(self, agent_type: Union[AgentType, str]) -> AgentType:
        """Resolve an AgentType from either an enum or string value."""
        if isinstance(agent_type, AgentType):
            return agent_type
        if isinstance(agent_type, str):
            return AgentType(agent_type)
        raise TypeError(f"Cannot resolve agent type: {agent_type}")

    def get_agent(self, agent_type: Union[AgentType, str]) -> BaseAgent:
        """Get or create an agent instance by type.

        Args:
            agent_type: AgentType enum or its string value.

        Returns:
            A cached agent instance.
        """
        resolved = self._resolve_type(agent_type)
        if resolved not in self._instances:
            agent_cls = self._agent_classes[resolved]
            self._instances[resolved] = agent_cls(llm_service=self._llm)
        return self._instances[resolved]

    @property
    def available_agents(self) -> list[str]:
        return [t.value for t in self._agent_classes.keys()]


# Module-level singleton — initialized lazily when llm_service is ready
registry: AgentRegistry = None  # type: ignore[assignment]


def init_registry(llm_service: LLMService) -> AgentRegistry:
    """Initialize the global agent registry with an LLM service."""
    global registry
    if registry is None:
        registry = AgentRegistry(llm_service)
    return registry
