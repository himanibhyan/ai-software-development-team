from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AppException
from app.graph.state import create_initial_state


def _make_state(**overrides):
    state = create_initial_state(
        idea="Build a REST API for task management",
        constraints=None,
    )
    state.update(overrides)
    return state


class TestGetRegistry:
    def test_returns_registry(self):
        from app.graph.nodes import _get_registry
        registry_obj = MagicMock()
        with patch("app.graph.nodes.agent_registry", registry_obj):
            assert _get_registry() == registry_obj

    def test_raises_when_none(self):
        from app.graph.nodes import _get_registry
        with patch("app.graph.nodes.agent_registry", None):
            with pytest.raises(AppException, match="not initialized"):
                _get_registry()


class TestErrorUpdates:
    def test_builds_error_dict(self):
        from app.graph.nodes import _error_updates
        state = _make_state(current_agent="developer")
        result = _error_updates(state, "development", "Something broke")

        assert result["status"] == "failed"
        assert len(result["errors"]) == 1
        assert result["errors"][0]["step"] == "development"
        assert result["errors"][0]["message"] == "Something broke"
        assert result["errors"][0]["agent"] == "developer"
        assert result["current_agent"] is None
        assert result["revision"] == state["revision"] + 1


class TestValidateInputNode:
    async def test_valid_input_returns_running(self):
        from app.graph.nodes import validate_input_node
        state = _make_state()
        result = await validate_input_node(state)
        assert result["status"] == "running"
        assert result["revision"] == state["revision"] + 1

    async def test_short_input_returns_failed(self):
        from app.graph.nodes import validate_input_node
        state = _make_state(idea="short")
        result = await validate_input_node(state)
        assert result["status"] == "failed"
        assert len(result["errors"]) == 1

    async def test_skips_validation_in_resume_mode(self):
        from app.graph.nodes import validate_input_node
        state = _make_state(resume_mode=True, idea="short")
        result = await validate_input_node(state)
        assert result["status"] == "running"


class TestAgentNodes:
    @pytest.fixture
    def mock_agent(self):
        agent = AsyncMock()
        agent.process.return_value = {
            "requirements": {"title": "Test", "purpose": "Test purpose"},
        }
        return agent

    @pytest.fixture
    def mock_registry(self, mock_agent):
        registry = MagicMock()
        registry.get_agent.return_value = mock_agent
        return registry

    @pytest.fixture
    def state_with_project(self):
        return _make_state(current_agent="requirements")

    async def test_requirements_node_success(self, state_with_project, mock_registry):
        from app.graph.nodes import requirements_node
        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await requirements_node(state_with_project)

        assert "requirements" in str(result)
        assert result["completed_steps"] == ["requirements"]

    async def test_requirements_node_skipped_in_resume(self, state_with_project, mock_registry):
        from app.graph.nodes import requirements_node
        state_with_project["resume_mode"] = True
        state_with_project["completed_steps"] = ["requirements"]
        state_with_project["requirements"] = {"title": "Existing"}

        result = await requirements_node(state_with_project)
        assert result == {"current_agent": "requirements"}
        mock_registry.get_agent.assert_not_called()

    async def test_requirements_node_failure(self, state_with_project, mock_registry):
        from app.graph.nodes import requirements_node
        mock_registry.get_agent.return_value.process.side_effect = Exception("fail")

        with patch("app.graph.nodes.agent_registry", mock_registry):
            result = await requirements_node(state_with_project)

        assert result["status"] == "failed"
        assert len(result["errors"]) >= 1

    async def test_architect_node_success(self, mock_registry):
        from app.graph.nodes import architect_node
        agent = mock_registry.get_agent.return_value
        agent.process.return_value = {
            "architecture": {"pattern": "microservices", "overview": "Overview of the architecture with all components"},
        }
        state = _make_state(requirements={"title": "Req"})

        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await architect_node(state)

        assert result["completed_steps"] == ["architecture"]

    async def test_architect_node_skipped_in_resume(self, mock_registry):
        from app.graph.nodes import architect_node
        state = _make_state(
            resume_mode=True,
            completed_steps=["architecture"],
            architecture={"pattern": "microservices", "overview": "Overview of the architecture with all components"},
        )

        result = await architect_node(state)
        assert result == {"current_agent": "architect"}
        mock_registry.get_agent.assert_not_called()

    async def test_developer_node_success(self, mock_registry):
        from app.graph.nodes import developer_node
        agent = mock_registry.get_agent.return_value
        agent.process.return_value = {
            "source_code": {"files": [{"path": "main.py", "content": "print('hello')"}]},
        }
        state = _make_state(architecture={"pattern": "microservices", "overview": "Overview of the architecture with all components"})

        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await developer_node(state)

        assert "development" in result.get("completed_steps", [])

    async def test_developer_node_adds_completed_steps(self, mock_registry):
        from app.graph.nodes import developer_node
        agent = mock_registry.get_agent.return_value
        agent.process.return_value = {"source_code": {"files": []}}
        state = _make_state()

        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await developer_node(state)

        assert result["completed_steps"] == ["development"]

    async def test_code_review_node_increments_attempts(self, mock_registry):
        from app.graph.nodes import code_review_node
        agent = mock_registry.get_agent.return_value
        agent.process.return_value = {
            "review_report": {
                "summary": "Review summary here with enough detail",
                "overall_score": 8.0,
                "comments": [],
                "strengths": [],
                "weaknesses": [],
                "security_concerns": [],
            },
        }
        state = _make_state(
            source_code={"files": [{"path": "main.py", "content": "print('hello')"}]},
            review_attempts=1,
        )

        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await code_review_node(state)

        assert result["review_attempts"] == 2
        assert result["completed_steps"] == ["code_review"]

    async def test_code_review_node_skipped_in_resume(self, mock_registry):
        from app.graph.nodes import code_review_node
        state = _make_state(
            resume_mode=True,
            completed_steps=["code_review"],
            review_report={"summary": "Review summary here with enough detail", "overall_score": 8.0, "comments": [], "strengths": [], "weaknesses": [], "security_concerns": []},
        )

        result = await code_review_node(state)
        assert result == {"current_agent": "code_review"}
        mock_registry.get_agent.assert_not_called()

    async def test_tester_node_success(self, mock_registry):
        from app.graph.nodes import tester_node
        agent = mock_registry.get_agent.return_value
        agent.process.return_value = {
            "test_suite": {"test_framework": "pytest", "test_cases": []},
        }
        state = _make_state(source_code={"files": []})

        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await tester_node(state)

        assert result["completed_steps"] == ["testing"]

    async def test_tester_node_skipped_in_resume(self, mock_registry):
        from app.graph.nodes import tester_node
        state = _make_state(
            resume_mode=True,
            completed_steps=["testing"],
            test_suite={"test_framework": "pytest", "test_cases": []},
        )

        result = await tester_node(state)
        assert result == {"current_agent": "tester"}
        mock_registry.get_agent.assert_not_called()

    async def test_documentation_node_success(self, mock_registry):
        from app.graph.nodes import documentation_node
        agent = mock_registry.get_agent.return_value
        agent.process.return_value = {
            "documentation": {"readme": "# Project", "setup_guide": "pip install"},
        }
        state = _make_state(
            source_code={"files": []},
            test_suite={"test_framework": "pytest", "test_cases": []},
        )

        with patch("app.graph.nodes.agent_registry", mock_registry):
            with patch("app.graph.nodes._save_step_checkpoint"):
                result = await documentation_node(state)

        assert result["completed_steps"] == ["documentation"]

    async def test_documentation_node_skipped_in_resume(self, mock_registry):
        from app.graph.nodes import documentation_node
        state = _make_state(
            resume_mode=True,
            completed_steps=["documentation"],
            documentation={"readme": "# Project", "setup_guide": "pip install"},
        )

        result = await documentation_node(state)
        assert result == {"current_agent": "documentation"}
        mock_registry.get_agent.assert_not_called()

    async def test_all_agents_return_error_updates_on_failure(self, mock_registry):
        from app.graph.nodes import (
            architect_node,
            code_review_node,
            developer_node,
            documentation_node,
            requirements_node,
            tester_node,
        )
        mock_registry.get_agent.return_value.process.side_effect = Exception("boom")

        for node_fn in [requirements_node, architect_node, developer_node, code_review_node, tester_node, documentation_node]:
            mock_registry.reset_mock()
            state = _make_state()
            with patch("app.graph.nodes.agent_registry", mock_registry):
                result = await node_fn(state)
            assert result["status"] == "failed", f"{node_fn.__name__} should return failed status"
            assert len(result["errors"]) >= 1, f"{node_fn.__name__} should include errors"


class TestPersistenceNode:
    async def test_completes_pipeline(self):
        from app.graph.nodes import persistence_node
        state = _make_state(
            source_code={
                "files": [
                    {"path": "main.py", "content": "print('hello')", "language": "python"},
                ],
            },
            token_usage=[{"agent": "test", "total_tokens": 100}],
        )

        mock_storage = MagicMock()
        with patch("app.services.storage_service.storage_service", mock_storage):
            result = await persistence_node(state)

        assert result["status"] == "completed"
        assert result["current_agent"] is None
        assert result["revision"] == state["revision"] + 1
        assert mock_storage.save_checkpoint.called
        assert mock_storage.save_execution_log.called
        assert mock_storage.save_generated_code.called
        assert mock_storage.save_manifest.called

    async def test_no_source_code_files(self):
        from app.graph.nodes import persistence_node
        state = _make_state(source_code={"files": []})

        mock_storage = MagicMock()
        with patch("app.services.storage_service.storage_service", mock_storage):
            result = await persistence_node(state)

        assert result["status"] == "completed"
        mock_storage.save_generated_code.assert_not_called()

    async def test_source_code_not_a_dict(self):
        from app.graph.nodes import persistence_node
        state = _make_state(source_code=None)

        mock_storage = MagicMock()
        with patch("app.services.storage_service.storage_service", mock_storage):
            result = await persistence_node(state)

        assert result["status"] == "completed"

    async def test_storage_exception_is_swallowed(self):
        from app.graph.nodes import persistence_node
        state = _make_state(source_code={"files": [{"path": "m.py", "content": "x"}]})

        mock_storage = MagicMock()
        mock_storage.save_checkpoint.side_effect = Exception("disk full")
        with patch("app.services.storage_service.storage_service", mock_storage):
            result = await persistence_node(state)

        assert result["status"] == "completed"

    async def test_agent_results_contains_summary(self):
        from app.graph.nodes import persistence_node
        state = _make_state(
            source_code={"files": []},
            token_usage=[{"agent": "dev", "total_tokens": 50}, {"agent": "review", "total_tokens": 30}],
        )

        with patch("app.services.storage_service.storage_service", MagicMock()):
            result = await persistence_node(state)

        assert len(result["agent_results"]) == 1
        summary = result["agent_results"][0]
        assert summary["agent"] == "persistence"
        assert summary["total_tokens"] == 80


class TestErrorNode:
    async def test_returns_failed_status(self):
        from app.graph.nodes import error_node
        state = _make_state(errors=[{"step": "test", "message": "critical failure"}])
        result = await error_node(state)

        assert result["status"] == "failed"
        assert result["current_agent"] is None
        assert result["end_time"] is not None

    async def test_increments_revision(self):
        from app.graph.nodes import error_node
        state = _make_state(errors=[{"step": "test", "message": "fail"}])
        result = await error_node(state)
        assert result["revision"] == state["revision"] + 1


class TestSaveStepCheckpoint:
    def test_saves_checkpoint_and_log(self):
        from app.graph.nodes import _save_step_checkpoint
        state = _make_state(project_id=str(uuid4()))

        mock_storage = MagicMock()
        with patch("app.services.storage_service.storage_service", mock_storage):
            _save_step_checkpoint(state, "test_agent")

        mock_storage.save_checkpoint.assert_called_once()
        mock_storage.save_execution_log.assert_called_once()

    def test_swallows_exception(self):
        from app.graph.nodes import _save_step_checkpoint
        state = _make_state(project_id=str(uuid4()))

        mock_storage = MagicMock()
        mock_storage.save_checkpoint.side_effect = Exception("fail")
        with patch("app.services.storage_service.storage_service", mock_storage):
            _save_step_checkpoint(state, "test_agent")

    def test_creates_valid_execution_log(self):
        from app.graph.nodes import _save_step_checkpoint
        pid = str(uuid4())
        state = _make_state(
            project_id=pid,
            status="running",
            completed_steps=["requirements"],
            pending_steps=["architecture"],
            errors=[{"step": "test", "message": "warn"}],
            warnings=[{"step": "test", "message": "note"}],
        )

        mock_storage = MagicMock()
        with patch("app.services.storage_service.storage_service", mock_storage):
            _save_step_checkpoint(state, "developer")

        args, _ = mock_storage.save_execution_log.call_args
        assert args[0] == pid
        log = args[1]
        assert log["agent"] == "developer"
        assert log["status"] == "running"
        assert log["revision"] == 0
        assert log["error_count"] == 1
        assert log["warning_count"] == 1
