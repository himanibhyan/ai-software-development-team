from __future__ import annotations

from app.agents.base import BaseAgent
from app.agents.prompts.code_review import SYSTEM_PROMPT
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.models.domain.project import CodeReviewReport


class CodeReviewAgent(BaseAgent):
    """Reviews generated source code for quality, security, and correctness."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.CODE_REVIEW

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def output_model(self) -> type[CodeReviewReport]:
        return CodeReviewReport

    def build_user_prompt(self, state: GraphState) -> str:
        base = super().build_user_prompt(state)
        source = state.get("source_code", {})
        files_text = ""
        if source:
            file_list = source.get("files", [])
            files_text = "\n\n## Source Code to Review\n"
            for f in file_list:
                path = f.get("path", "unknown")
                content = f.get("content", "")
                lang = f.get("language", "text")
                files_text += f"\n### {path} ({lang})\n```{lang}\n{content}\n```\n"

        return (
            f"{base}\n\n"
            f"## Requirements Context\n"
            f"{state.get('requirements', {}).get('purpose', 'N/A')}\n"
            f"{files_text}\n"
            f"## Instructions\n"
            f"Review every file thoroughly. Check for correctness, security vulnerabilities, "
            f"performance issues, error handling gaps, and adherence to best practices. "
            f"Provide a numeric score and specific, actionable feedback."
        )

    def _validate_output(self, output: CodeReviewReport) -> CodeReviewReport:
        if output.overall_score < 0 or output.overall_score > 10:
            raise ValueError(
                f"Score must be between 0 and 10, got {output.overall_score}"
            )
        return output
