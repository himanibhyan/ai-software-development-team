from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.agents.prompts.documentation import SYSTEM_PROMPT
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.models.domain.project import Documentation


class DocumentationAgent(BaseAgent):
    """Generates comprehensive technical documentation."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.DOCUMENTATION

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def output_model(self) -> type[Documentation]:
        return Documentation

    def build_user_prompt(self, state: GraphState) -> str:
        base = super().build_user_prompt(state)

        reqs = state.get("requirements", {})
        arch = state.get("architecture", {})
        source = state.get("source_code", {})
        tests = state.get("test_suite", {})

        source_overview = ""
        if source:
            files = source.get("files", [])
            file_list = "\n".join(
                f"  - {f.get('path', 'unknown')} ({f.get('language', 'text')})"
                for f in files
            )
            source_overview = f"\n### Project Structure\n{file_list}"

        test_overview = ""
        if tests:
            tcs = tests.get("test_cases", [])
            test_overview = (
                f"\n### Test Suite\n"
                f"Framework: {tests.get('test_framework', 'N/A')}\n"
                f"Test Cases: {len(tcs)}\n"
            )

        return (
            f"{base}\n\n"
            f"## Requirements\n"
            f"Title: {reqs.get('title', 'N/A')}\n"
            f"Purpose: {reqs.get('purpose', 'N/A')}\n\n"
            f"## Architecture\n"
            f"Pattern: {arch.get('architecture_pattern', 'N/A')}\n"
            f"Components: {[c.get('name') for c in arch.get('components', [])]}\n\n"
            f"## Source Code\n{source_overview}\n\n"
            f"{test_overview}\n"
            f"## Instructions\n"
            f"Generate complete documentation for this project. "
            f"The README must include setup, usage, and configuration instructions. "
            f"The API documentation must document all endpoints. "
            f"Write for a developer audience — be precise and thorough."
        )
