from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.agents.tester_agent import TesterAgent
from app.models.domain.enums import AgentType
from app.models.domain.project import TestCase, TestSuite
from app.services.llm_service import LLMService


def _make_state(**overrides) -> dict:
    state: dict = {
        "project_id": str(uuid4()),
        "idea": "Build a CLI todo app",
        "constraints": None,
        "status": "running",
        "current_agent": None,
        "errors": [],
        "warnings": [],
        "requirements": {
            "title": "Todo App",
            "functional_requirements": [
                {"id": "FR-01", "description": "Add tasks", "category": "core", "priority": "P0"}
            ],
        },
        "source_code": {
            "root": "todo-app",
            "files": [
                {"path": "src/todo.py", "content": "def add_task(name): return name", "language": "python"},
                {"path": "src/main.py", "content": "def main(): print('hi')", "language": "python"},
            ],
        },
        "architecture": None,
        "test_suite": None,
        "documentation": None,
        "review_report": None,
        "start_time": "2025-01-01T00:00:00",
        "end_time": None,
        "revision": 0,
        "token_usage": [],
        "agent_results": [],
        "review_attempts": 0,
        "max_review_attempts": 3,
        "resume_mode": False,
        "completed_steps": [],
        "pending_steps": [],
    }
    state.update(overrides)
    return state


@pytest.fixture
def agent():
    llm = MagicMock(spec=LLMService)
    return TesterAgent(llm)


class TestTesterAgentProperties:
    def test_agent_type(self, agent: TesterAgent):
        assert agent.agent_type == AgentType.TESTER

    def test_system_prompt(self, agent: TesterAgent):
        assert "QA Engineer" in agent.system_prompt
        assert "Good example" in agent.system_prompt
        assert "Bad example" in agent.system_prompt

    def test_output_model(self, agent: TesterAgent):
        assert agent.output_model == TestSuite


class TestValidateOutput:
    def test_rejects_empty_test_cases(self, agent: TesterAgent):
        suite = TestSuite(test_framework="pytest", test_cases=[])
        with pytest.raises(ValueError, match="at least one test case"):
            agent._validate_output(suite)

    def test_rejects_missing_framework(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="",
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="unit"),
            ],
        )
        with pytest.raises(ValueError, match="framework must be specified"):
            agent._validate_output(suite)

    def test_rejects_low_coverage_target(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            coverage_target=0.5,
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="unit"),
            ],
        )
        with pytest.raises(ValueError, match="Coverage target"):
            agent._validate_output(suite)

    def test_rejects_empty_code(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="", type="unit"),
            ],
        )
        with pytest.raises(ValueError, match="empty code"):
            agent._validate_output(suite)

    def test_rejects_empty_file_path(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="X", file_path="", code="pass", type="unit"),
            ],
        )
        with pytest.raises(ValueError, match="no file_path"):
            agent._validate_output(suite)

    def test_rejects_duplicate_test_names(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="A", file_path="t1.py", code="pass", type="unit"),
                TestCase(name="test_x", description="B", file_path="t2.py", code="pass", type="unit"),
            ],
        )
        with pytest.raises(ValueError, match="Duplicate"):
            agent._validate_output(suite)

    def test_rejects_invalid_test_type(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="e2e"),
            ],
        )
        with pytest.raises(ValueError, match="invalid type"):
            agent._validate_output(suite)

    def test_accepts_valid_suite(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            coverage_target=0.85,
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="unit"),
            ],
        )
        result = agent._validate_output(suite)
        assert result is suite


class TestSanitizeOutput:
    def test_strips_whitespace(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="  PYTEST  ",
            coverage_target=0.9,
            test_cases=[
                TestCase(
                    name="  test_x  ", description="  X  ", file_path="  t.py  ", code="  pass  ", type="  UNIT  "
                ),
            ],
        )
        result = agent._sanitize_output(suite)
        assert result.test_framework == "pytest"
        assert result.test_cases[0].name == "test_x"
        assert result.test_cases[0].code == "pass"
        assert result.test_cases[0].type == "unit"

    def test_normalizes_backslashes(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="X", file_path="tests\\test_x.py", code="pass", type="unit"),
            ],
        )
        result = agent._sanitize_output(suite)
        assert "/" in result.test_cases[0].file_path
        assert "\\" not in result.test_cases[0].file_path

    def test_deduplicates_by_name(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="v1", file_path="t1.py", code="pass", type="unit"),
                TestCase(name="test_x", description="v2", file_path="t2.py", code="pass", type="unit"),
            ],
        )
        result = agent._sanitize_output(suite)
        assert len(result.test_cases) == 1

    def test_ensures_minimum_coverage(self, agent: TesterAgent):
        suite = TestSuite(
            test_framework="pytest",
            coverage_target=0.3,
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="unit"),
            ],
        )
        result = agent._sanitize_output(suite)
        assert result.coverage_target >= 0.8


class TestBuildStateUpdates:
    def test_includes_sanitized_output(self, agent: TesterAgent):
        state = _make_state()
        suite = TestSuite(
            test_framework="  PYTEST  ",
            coverage_target=0.9,
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="  UNIT  "),
            ],
        )
        updates = agent._build_state_updates(state, suite, {"prompt_tokens": 5, "completion_tokens": 3})
        test_suite = updates["test_suite"]
        assert test_suite["test_framework"] == "pytest"
        assert test_suite["test_cases"][0]["type"] == "unit"

    def test_includes_token_usage(self, agent: TesterAgent):
        state = _make_state()
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(name="test_x", description="X", file_path="t.py", code="pass", type="unit"),
            ],
        )
        updates = agent._build_state_updates(state, suite, {"prompt_tokens": 5, "completion_tokens": 3})
        assert len(updates["token_usage"]) == 1
        assert updates["token_usage"][0]["agent"] == "tester"


class TestBuildUserPrompt:
    def test_includes_source_code(self, agent: TesterAgent):
        state = _make_state()
        prompt = agent.build_user_prompt(state)
        assert "src/todo.py" in prompt
        assert "src/main.py" in prompt
        assert "def add_task" in prompt

    def test_includes_requirements_count(self, agent: TesterAgent):
        state = _make_state()
        prompt = agent.build_user_prompt(state)
        assert "FRs: 1" in prompt
