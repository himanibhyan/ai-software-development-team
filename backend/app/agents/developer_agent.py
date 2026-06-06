from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.prompts.developer import SYSTEM_PROMPT
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.models.domain.project import ProjectTree


class DeveloperAgent(BaseAgent):
    """Generates complete source code from requirements and architecture."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.DEVELOPER

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def output_model(self) -> type[ProjectTree]:
        return ProjectTree

    def build_user_prompt(self, state: GraphState) -> str:
        base = super().build_user_prompt(state)
        reqs = state.get("requirements", {})
        arch = state.get("architecture", {})

        review_feedback = ""
        if state.get("review_report"):
            review_feedback = (
                f"## Previous Code Review Feedback\n"
                f"Note: This is a revision based on the following review:\n"
                f"{state['review_report'].get('summary', '')}\n"
                f"Weaknesses to address: {state['review_report'].get('weaknesses', [])}\n"
                f"Security concerns: {state['review_report'].get('security_concerns', [])}\n"
                f"Please fix all issues mentioned above.\n"
            )

        return (
            f"{base}\n\n"
            f"## Requirements Summary\n"
            f"Title: {reqs.get('title', 'N/A')}\n"
            f"Purpose: {reqs.get('purpose', 'N/A')}\n"
            f"Functional Requirements: {len(reqs.get('functional_requirements', []))}\n\n"
            f"## Architecture Summary\n"
            f"Pattern: {arch.get('architecture_pattern', 'N/A')}\n"
            f"Components: {[c.get('name') for c in arch.get('components', [])]}\n"
            f"Tech Stack: {arch.get('tech_stack', {})}\n\n"
            f"{review_feedback}"
            f"## Instructions\n"
            f"Generate a complete, working implementation. "
            f"Include all source files needed for a functional project. "
            f"Code MUST be syntactically valid and all imports must resolve correctly."
        )

    def _validate_output(self, output: ProjectTree) -> ProjectTree:
        if not output.files:
            raise ValueError("Code generation produced zero files")
        has_main = any("main" in f.path for f in output.files)
        if not has_main:
            raise ValueError("No main entry point found in generated code")
        return output
