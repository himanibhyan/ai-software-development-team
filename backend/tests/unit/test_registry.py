from __future__ import annotations

import pytest

from app.agents.registry import AgentRegistry
from app.agents.requirements_agent import RequirementsAgent
from app.agents.architect_agent import ArchitectAgent
from app.agents.developer_agent import DeveloperAgent
from app.agents.code_review_agent import CodeReviewAgent
from app.agents.tester_agent import TesterAgent
from app.agents.documentation_agent import DocumentationAgent
from app.models.domain.enums import AgentType


class TestAgentRegistry:
    def test_registry_initialization(self):
        registry = AgentRegistry(llm_service=None)  # type: ignore
        assert len(registry._agent_classes) == 6

    def test_get_agent_by_enum(self):
        registry = AgentRegistry(llm_service=None)
        agent = registry.get_agent(AgentType.REQUIREMENTS)
        assert isinstance(agent, RequirementsAgent)

    def test_get_agent_by_string(self):
        registry = AgentRegistry(llm_service=None)
        agent = registry.get_agent("requirements")
        assert isinstance(agent, RequirementsAgent)

    def test_get_agent_caches_instance(self):
        registry = AgentRegistry(llm_service=None)
        agent1 = registry.get_agent("architect")
        agent2 = registry.get_agent("architect")
        assert agent1 is agent2

    def test_get_all_agent_types(self):
        registry = AgentRegistry(llm_service=None)
        agent = registry.get_agent("architect")
        assert isinstance(agent, ArchitectAgent)
        agent = registry.get_agent("developer")
        assert isinstance(agent, DeveloperAgent)
        agent = registry.get_agent("code_review")
        assert isinstance(agent, CodeReviewAgent)
        agent = registry.get_agent("tester")
        assert isinstance(agent, TesterAgent)
        agent = registry.get_agent("documentation")
        assert isinstance(agent, DocumentationAgent)

    def test_invalid_agent_type_raises(self):
        registry = AgentRegistry(llm_service=None)
        with pytest.raises(ValueError):
            registry.get_agent("nonexistent")

    def test_available_agents(self):
        registry = AgentRegistry(llm_service=None)
        agents = registry.available_agents
        assert "requirements" in agents
        assert "architect" in agents
        assert "developer" in agents
        assert "code_review" in agents
        assert "tester" in agents
        assert "documentation" in agents
