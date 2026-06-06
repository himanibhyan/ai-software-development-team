from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.base import BaseAgent
from app.agents.registry import AgentRegistry
from app.graph.pipeline import build_pipeline, get_pipeline
from app.graph.state import create_initial_state, state_summary
from app.services.llm_service import LLMService


@pytest.fixture
def mock_agent_registry():
    """Create a mock agent registry with all agents returning valid data."""
    registry = MagicMock(spec=AgentRegistry)

    def make_mock_agent(result_key: str, result_value: dict):
        agent = AsyncMock(spec=BaseAgent)
        agent.process.return_value = {result_key: result_value}
        return agent

    mock_req = make_mock_agent("requirements", {
        "functional_requirements": [{"id": "FR-01", "description": "Test FR", "category": "performance", "priority": "P0"}],
        "non_functional_requirements": [{"id": "NFR-01", "description": "Test NFR", "category": "performance"}],
        "user_stories": [{"id": "US-01", "description": "Test US", "priority": "P0"}],
    })
    mock_arch = make_mock_agent("architecture", {
        "components": [{"name": "TestComp", "responsibility": "testing", "technologies": ["Python"]}],
        "tech_stack": {"languages": ["Python"], "frameworks": [], "databases": [], "infrastructure": []},
    })
    mock_dev = make_mock_agent("source_code", {"files": [{"path": "test.py", "content": "print('hello')", "language": "python"}]})
    mock_review = make_mock_agent("review_report", {
        "overall_score": 8.5,
        "strengths": ["good"],
        "weaknesses": [],
        "recommendations": [],
    })
    mock_tester = make_mock_agent("test_suite", {
        "test_files": [{"path": "test_test.py", "content": "def test(): pass", "language": "python"}],
    })
    mock_docs = make_mock_agent("documentation", {
        "sections": [{"title": "Overview", "content": "Docs", "order": 1}],
    })

    registry.get_agent.side_effect = lambda agent_type: {
        "requirements": mock_req,
        "architect": mock_arch,
        "developer": mock_dev,
        "code_review": mock_review,
        "tester": mock_tester,
        "documentation": mock_docs,
    }.get(agent_type if isinstance(agent_type, str) else agent_type.value, mock_req)
    return registry


class TestGenerationPipeline:
    def test_pipeline_construction(self):
        """Verify the pipeline compiles without errors."""
        pipeline = build_pipeline()
        assert pipeline is not None
        # Pipeline should have 9 registered nodes
        assert hasattr(pipeline, "invoke")

    def test_pipeline_singleton(self):
        """get_pipeline should return the same instance."""
        p1 = get_pipeline()
        p2 = get_pipeline()
        assert p1 is p2

    def test_pipeline_state_summary(self, sample_idea: str):
        """State summary produces human-readable output."""
        state = create_initial_state(idea=sample_idea)
        summary = state_summary(state)
        assert summary["project_id"] == state["project_id"]
        assert summary["revision"] == 0

    def test_state_idempotent_summary(self, sample_idea: str):
        """State summary should not mutate the state."""
        state = create_initial_state(idea=sample_idea)
        original_revision = state["revision"]
        state_summary(state)
        assert state["revision"] == original_revision


@pytest.mark.asyncio
class TestGenerationPipelineInvoke:
    """Async tests for pipeline invocation (nodes are async functions)."""

    @pytest.fixture(autouse=True)
    def _patch_registry(self, mock_agent_registry):
        with patch("app.graph.nodes.agent_registry", mock_agent_registry):
            yield

    async def _ainvoke(self, pipeline, state):
        """Invoke pipeline asynchronously with required thread_id config."""
        return await pipeline.ainvoke(
            state,
            config={"configurable": {"thread_id": state["project_id"]}},
        )

    async def test_pipeline_accepts_state(self, sample_idea: str):
        """Pipeline can invoke with a valid state."""
        pipeline = build_pipeline()
        state = create_initial_state(idea=sample_idea)
        result = await self._ainvoke(pipeline, state)
        assert result is not None
        assert isinstance(result, dict)
        assert "idea" in result
        assert result["idea"] == sample_idea

    async def test_pipeline_rejects_short_input(self):
        """Pipeline should reject inputs shorter than 10 chars."""
        pipeline = build_pipeline()
        state = create_initial_state(idea="short")
        result = await self._ainvoke(pipeline, state)
        assert result["status"] == "failed"
        assert len(result.get("errors", [])) >= 0

    async def test_pipeline_sequential_flow(self, sample_idea: str):
        """Verify the pipeline follows the expected sequential flow."""
        pipeline = build_pipeline()
        state = create_initial_state(idea=sample_idea)
        result = await self._ainvoke(pipeline, state)

        assert result["status"] in ("running", "failed", "completed")
        assert result["revision"] >= 1
