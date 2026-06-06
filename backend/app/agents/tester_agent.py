from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.prompts.tester import SYSTEM_PROMPT
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.models.domain.project import TestSuite


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
        if not output.test_cases:
            raise ValueError("Test suite must contain at least one test case")
        return output
