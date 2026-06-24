from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.agents.prompts.tester import SYSTEM_PROMPT
from app.core.logging import get_logger
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.models.domain.project import TestCase, TestSuite

logger = get_logger(__name__)


class TesterAgent(BaseAgent):
    """Generates comprehensive test suites for the source code."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.TESTER

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def output_model(self) -> type[TestSuite]:
        return TestSuite

    def build_user_prompt(self, state: GraphState) -> str:
        base = super().build_user_prompt(state)
        source = state.get("source_code", {})
        files_text = ""
        if source:
            files_text = "\n\n## Source Code Under Test\n"
            for f in source.get("files", []):
                path = f.get("path", "unknown")
                content = f.get("content", "")
                lang = f.get("language", "text")
                files_text += f"\n### {path}\n```{lang}\n{content}\n```\n"

        reqs = state.get("requirements", {})

        return (
            f"{base}\n\n"
            f"## Requirements to Validate\n"
            f"FRs: {len(reqs.get('functional_requirements', []))} requirements\n"
            f"NFRs: {len(reqs.get('non_functional_requirements', []))} requirements\n"
            f"{files_text}\n"
            f"## Instructions\n"
            f"Generate a complete test suite for the code above. "
            f"Include both unit tests and integration tests. "
            f"Each test must be valid, runnable code. "
            f"Aim for >80% code coverage. Test all functional requirements."
        )

    def _validate_output(self, output: TestSuite) -> TestSuite:
        errors: list[str] = []

        if not output.test_cases:
            raise ValueError("Test suite must contain at least one test case")

        if not output.test_framework.strip():
            errors.append("Test framework must be specified")

        if output.coverage_target < 0.8:
            errors.append(f"Coverage target too low: {output.coverage_target} (minimum 0.8)")

        seen_names: set[str] = set()
        for i, tc in enumerate(output.test_cases):
            if not tc.file_path.strip():
                errors.append(f"Test case '{tc.name}' at index {i} has no file_path")
            if not tc.code.strip():
                errors.append(f"Test case '{tc.name}' at index {i} has empty code")
            if tc.name in seen_names:
                errors.append(f"Duplicate test name: '{tc.name}'")
            seen_names.add(tc.name)
            if tc.type not in ("unit", "integration"):
                errors.append(f"Test case '{tc.name}' has invalid type: '{tc.type}' (must be 'unit' or 'integration')")

        if errors:
            error_summary = "\n".join(f"  - {e}" for e in errors)
            logger.warning(
                "tester_validation_errors",
                error_count=len(errors),
                test_count=len(output.test_cases),
            )
            raise ValueError(f"Tester validation failed with {len(errors)} issue(s):\n{error_summary}")

        return output

    def _sanitize_output(self, output: TestSuite) -> TestSuite:
        seen: dict[str, TestCase] = {}
        for tc in output.test_cases:
            if tc.name in seen:
                continue
            seen[tc.name] = TestCase(
                name=tc.name.strip(),
                description=tc.description.strip(),
                file_path=tc.file_path.strip().replace("\\", "/"),
                code=tc.code.strip(),
                type=tc.type.strip().lower(),
            )
        sorted_cases = sorted(seen.values(), key=lambda x: x.name)
        return TestSuite(
            test_framework=output.test_framework.strip().lower(),
            test_config=output.test_config,
            test_cases=sorted_cases,
            coverage_target=max(output.coverage_target, 0.8),
        )

    def _build_state_updates(
        self,
        state: GraphState,
        output: TestSuite,
        token_usage: dict[str, int],
    ) -> dict[str, Any]:
        sanitized = self._sanitize_output(output)
        field = self._state_field()
        updates: dict[str, Any] = {
            field: sanitized.model_dump(),
            "current_agent": self.agent_type.value,
            "revision": state["revision"] + 1,
        }
        if token_usage:
            updates["token_usage"] = [{"agent": self.agent_type.value, **token_usage}]
        return updates
