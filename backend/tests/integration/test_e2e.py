from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.agents.base import BaseAgent
from app.agents.registry import AgentRegistry
from app.graph.pipeline import get_pipeline
from app.graph.state import create_initial_state

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STORAGE_DIR = PROJECT_ROOT / "storage"
CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"


def _make_mock_agent(result_key: str, result_value: dict):
    agent = AsyncMock(spec=BaseAgent)
    agent.process.return_value = {result_key: result_value}
    return agent


@pytest.fixture
def mock_registry():
    """Create a mock agent registry with all agents returning valid data."""
    registry = MagicMock(spec=AgentRegistry)

    registry.get_agent.side_effect = lambda agent_type: {
        "requirements": _make_mock_agent(
            "requirements",
            {
                "title": "Todo App Requirements",
                "functional_requirements": [
                    {"id": "FR-01", "description": "Add tasks", "category": "core", "priority": "P0"},
                ],
                "non_functional_requirements": [
                    {"id": "NFR-01", "description": "CLI app", "category": "usability"},
                ],
                "user_stories": [
                    {
                        "id": "US-01",
                        "description": "As a user, I want to add tasks so that I can track them",
                        "priority": "P0",
                    },
                ],
            },
        ),
        "architect": _make_mock_agent(
            "architecture",
            {
                "components": [
                    {"name": "CLI", "responsibility": "handle CLI args", "technologies": ["Python"]},
                ],
                "tech_stack": {"languages": ["Python"], "frameworks": [], "databases": ["JSON"], "infrastructure": []},
            },
        ),
        "developer": _make_mock_agent(
            "source_code",
            {
                "files": [
                    {"path": "todo.py", "content": "print('todo app')", "language": "python"},
                ],
            },
        ),
        "code_review": _make_mock_agent(
            "review_report",
            {
                "overall_score": 8.0,
                "strengths": ["Simple"],
                "weaknesses": [],
                "recommendations": ["Add tests"],
                "summary": "Good first version",
                "comments": [],
                "security_concerns": [],
            },
        ),
        "tester": _make_mock_agent(
            "test_suite",
            {
                "test_framework": "pytest",
                "test_cases": [
                    {"name": "test_add", "description": "Test adding a task", "type": "unit"},
                ],
                "test_files": [
                    {"path": "test_todo.py", "content": "def test_add(): pass", "language": "python"},
                ],
                "coverage_target": 80,
            },
        ),
        "documentation": _make_mock_agent(
            "documentation",
            {
                "sections": [
                    {"title": "Overview", "content": "A CLI todo app", "order": 1},
                    {"title": "Usage", "content": "python todo.py add", "order": 2},
                ],
            },
        ),
    }.get(agent_type if isinstance(agent_type, str) else agent_type.value)
    return registry


@pytest.fixture(autouse=True)
def _clean_storage():
    """Clean and recreate storage/checkpoint dirs before each test."""
    from app.services.storage_service import (
        BACKUPS_DIR,
        CHECKPOINTS_DIR,
        GENERATED_CODE_DIR,
        LOGS_DIR,
        MANIFESTS_DIR,
        STORAGE_DIR,
    )

    all_dirs = {STORAGE_DIR, CHECKPOINTS_DIR, GENERATED_CODE_DIR, MANIFESTS_DIR, LOGS_DIR, BACKUPS_DIR}
    for d in all_dirs:
        if d.exists():
            shutil.rmtree(d)
    for d in sorted(all_dirs, key=lambda p: str(p)):
        d.mkdir(parents=True, exist_ok=True)
    yield


@pytest.mark.asyncio
class TestEndToEndPipeline:
    """End-to-end test: API -> Celery task -> LangGraph -> DB -> disk."""

    async def test_full_pipeline_persists_to_disk(
        self,
        client: AsyncClient,
        sample_idea: str,
        mock_registry: MagicMock,
    ):
        """Create project via API, run pipeline with mocked agents,
        verify artifacts written to disk and DB."""
        # Step 1: Create project via API (writes to real PostgreSQL)
        create_resp = await client.post(
            "/api/v1/projects",
            json={"idea": sample_idea},
        )
        assert create_resp.status_code == 201
        project_id = create_resp.json()["project_id"]

        # Step 2: Run the pipeline with mocked agents
        pipeline = get_pipeline()
        state = create_initial_state(
            idea=sample_idea,
            project_id=uuid4(),
        )

        with patch(
            "app.graph.nodes.agent_registry_module.registry",
            mock_registry,
        ):
            final_state = await pipeline.ainvoke(
                state,
                config={"configurable": {"thread_id": str(state["project_id"])}},
            )

        # Step 3: Verify pipeline completed successfully
        assert final_state["status"] == "completed"
        assert final_state["revision"] >= 1
        assert final_state.get("requirements") is not None
        assert final_state.get("architecture") is not None
        assert final_state.get("source_code") is not None
        assert final_state.get("test_suite") is not None
        assert final_state.get("documentation") is not None
        assert final_state.get("review_report") is not None
        assert len(final_state.get("errors", [])) == 0

        # Step 4: Verify checkpoints written to disk
        pid = str(state["project_id"])
        checkpoint_files = list(CHECKPOINTS_DIR.glob(f"{pid}_*.json"))
        assert len(checkpoint_files) >= 1, f"No checkpoint files found for {pid} in {CHECKPOINTS_DIR}"

        # Step 5: Verify generated code on disk
        generated_code_dir = STORAGE_DIR / "generated_code"
        assert generated_code_dir.exists()
        project_code_dir = generated_code_dir / pid
        assert project_code_dir.exists(), f"No generated code dir for {pid}"
        code_files = list(project_code_dir.iterdir())
        assert len(code_files) >= 1, "No code files generated"

        # Step 6: Verify manifest on disk
        manifests_dir = STORAGE_DIR / "manifests"
        assert manifests_dir.exists()
        manifest_files = list(manifests_dir.glob(f"{pid}.json"))
        assert len(manifest_files) >= 1, "No manifest file found"

        # Step 7: Verify project still accessible via API
        get_resp = await client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == project_id
        assert data["idea"] == sample_idea

    async def test_failed_pipeline_still_returns_clean_result(
        self,
        client: AsyncClient,
        sample_idea: str,
    ):
        """When all agents fail, the pipeline returns failed status with error info."""
        create_resp = await client.post(
            "/api/v1/projects",
            json={"idea": sample_idea},
        )
        assert create_resp.status_code == 201

        pipeline = get_pipeline()
        state = create_initial_state(
            idea=sample_idea,
            project_id=uuid4(),
        )

        bad_registry = MagicMock(spec=AgentRegistry)
        failing_agent = AsyncMock(spec=BaseAgent)
        failing_agent.process.side_effect = Exception("LLM unavailable")
        bad_registry.get_agent.return_value = failing_agent

        with patch(
            "app.graph.nodes.agent_registry_module.registry",
            bad_registry,
        ):
            final_state = await pipeline.ainvoke(
                state,
                config={"configurable": {"thread_id": str(state["project_id"])}},
            )

        assert final_state["status"] == "failed"
        assert len(final_state.get("errors", [])) >= 1
        assert final_state["revision"] >= 1
