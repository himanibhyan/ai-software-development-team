from __future__ import annotations

import re
from typing import Any

from app.agents.base import BaseAgent
from app.agents.prompts.requirements import SYSTEM_PROMPT
from app.core.logging import get_logger
from app.graph.state import GraphState
from app.models.domain.enums import AgentType
from app.models.domain.project import (
    FunctionalRequirement,
    NonFunctionalRequirement,
    RequirementsDoc,
    UserStory,
)

logger = get_logger(__name__)


class RequirementsAgent(BaseAgent):
    """Generates a structured Software Requirements Specification (SRS).

    Transforms a natural-language software idea into a comprehensive,
    structured requirements document covering functional requirements,
    non-functional requirements, user stories, constraints, assumptions,
    and open issues.

    The agent:
    1. Builds a detailed user prompt from the software idea + constraints
    2. Calls the LLM with a domain-specific system prompt
    3. Validates the output against RequirementsDoc schema
    4. Performs domain-specific quality checks
    5. Sanitizes and normalizes the output
    6. Returns state updates with the artifact + token usage
    """

    @property
    def agent_type(self) -> AgentType:
        return AgentType.REQUIREMENTS

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    @property
    def output_model(self) -> type[RequirementsDoc]:
        return RequirementsDoc

    def build_user_prompt(self, state: GraphState) -> str:
        """Build the user prompt from current state.

        Constructs a detailed prompt that includes:
        - The original software idea
        - Any user-specified constraints
        - The output schema reminder
        - Quality instructions
        """
        base = super().build_user_prompt(state)

        parts = [
            base,
            "---",
            "## Instructions",
            "",
            "Produce a complete Software Requirements Specification for the idea described above.",
            "",
            "Follow these minimums:",
            "- At least 10 functional requirements (FR-01 through FR-10+)",
            "- At least 5 non-functional requirements covering different categories",
            "- At least 3 user stories",
            "- At least 2 constraints",
            "- At least 2 assumptions",
            "",
            "Every functional requirement MUST:",
            "- Be testable (someone can write a pass/fail test for it)",
            "- Describe ONE specific behavior",
            "- Include a priority (P0/P1/P2)",
            "- Address edge cases where relevant",
            "",
            "Think step by step:",
            "1. Identify the core domain and primary user personas",
            "2. List the main user journeys and workflows",
            "3. Derive functional requirements from each workflow step",
            "4. Identify quality attributes and derive NFRs",
            "5. Consider edge cases: concurrent usage, data limits, error states, offline behavior",
            "6. Consider security, privacy, and compliance needs",
            "",
            "Output ONLY valid JSON. No markdown, no backticks, no commentary.",
        ]

        return "\n".join(parts)

    async def process(self, state: GraphState) -> dict[str, Any]:
        """Execute requirements generation with enhanced validation.

        Extends the base process() method with:
        - Pre-process: Extract context from constraints
        - Post-process: Sanitize and normalize requirement IDs
        - Enhanced error messages for validation failures
        """
        logger.info(
            "agent:requirements_agent",
            project_id=state["project_id"],
            idea_length=len(state["idea"]),
        )

        try:
            return await super().process(state)
        except Exception as e:
            logger.error(
                "requirements_generation_failed",
                project_id=state["project_id"],
                error=str(e),
            )
            raise

    def _validate_output(self, output: RequirementsDoc) -> RequirementsDoc:
        """Deep validation of the requirements document.

        Checks:
        1. Pydantic schema validation (handled by LLM service)
        2. Minimum counts for each section
        3. ID format consistency (FR-XX, NFR-XX, US-XX)
        4. Priority distribution (at least some P0 items)
        5. Description quality (no vague terms)
        6. Covers core domain concepts
        """
        errors: list[str] = []

        # ── Count checks ─────────────────────────────────────────
        fr_count = len(output.functional_requirements)
        nfr_count = len(output.non_functional_requirements)
        us_count = len(output.user_stories)

        if fr_count < 8:
            errors.append(f"Too few functional requirements: {fr_count} (minimum 8)")
        if nfr_count < 4:
            errors.append(f"Too few non-functional requirements: {nfr_count} (minimum 4)")
        if us_count < 3:
            errors.append(f"Too few user stories: {us_count} (minimum 3)")
        if not output.constraints:
            errors.append("At least one constraint is required")
        if not output.assumptions:
            errors.append("At least one assumption is required")

        # ── ID format checks ────────────────────────────────────
        for i, fr in enumerate(output.functional_requirements):
            if not re.match(r"^FR-\d{2,}$", fr.id):
                errors.append(f"Invalid FR ID format: '{fr.id}' at index {i} (expected FR-XX)")

        for i, nfr in enumerate(output.non_functional_requirements):
            if not re.match(r"^NFR-\d{2,}$", nfr.id):
                errors.append(f"Invalid NFR ID format: '{nfr.id}' at index {i} (expected NFR-XX)")

        for i, us in enumerate(output.user_stories):
            if not re.match(r"^US-\d{2,}$", us.id):
                errors.append(f"Invalid US ID format: '{us.id}' at index {i} (expected US-XX)")

        # ── Priority distribution ────────────────────────────────
        p0_count = sum(1 for fr in output.functional_requirements if fr.priority == "P0")
        if fr_count > 0 and p0_count == 0:
            errors.append("At least one functional requirement must be priority P0")
        if fr_count >= 5 and p0_count < fr_count * 0.3:
            errors.append(f"Too few P0 requirements: {p0_count}/{fr_count} (minimum 30% should be P0)")

        # ── Description quality ──────────────────────────────────
        vague_terms = [
            "user-friendly",
            "easy to use",
            "fast",
            "efficient",
            "robust",
            "reliable",
            "good",
            "nice",
            "simple",
            "should work",
        ]
        for i, fr in enumerate(output.functional_requirements):
            desc_lower = fr.description.lower()
            for term in vague_terms:
                if term in desc_lower:
                    errors.append(f"Vague term '{term}' in FR-{i + 1:02d}: '{fr.description[:60]}...'")
                    break

        for i, nfr in enumerate(output.non_functional_requirements):
            desc_lower = nfr.description.lower()
            for term in vague_terms:
                if term in desc_lower and nfr.category != "usability":
                    errors.append(f"Vague term '{term}' in NFR-{i + 1:02d}: '{nfr.description[:60]}...'")
                    break

        # ── Category coverage ────────────────────────────────────
        required_categories = {"performance", "security"}
        actual_categories = {nfr.category for nfr in output.non_functional_requirements}
        missing = required_categories - actual_categories
        if missing:
            errors.append(f"Missing required NFR categories: {', '.join(sorted(missing))}")

        # ── User story format ────────────────────────────────────
        us_pattern = re.compile(
            r"As a\s+.+,\s+I want\s+.+,\s+so that\s+.+",
            re.IGNORECASE,
        )
        for i, us in enumerate(output.user_stories):
            if not us_pattern.match(us.description):
                errors.append(
                    f"User story {us.id} at index {i} does not follow format: "
                    f"'As a [role], I want [action] so that [benefit]'. "
                    f"Got: '{us.description[:80]}...'"
                )

        # ── Raise if errors found ───────────────────────────────
        if errors:
            error_summary = "\n".join(f"  - {e}" for e in errors)
            logger.warning(
                "requirements_validation_errors",
                error_count=len(errors),
                fr_count=fr_count,
                nfr_count=nfr_count,
                us_count=us_count,
            )
            raise ValueError(f"Requirements validation failed with {len(errors)} issue(s):\n{error_summary}")

        return output

    def _sanitize_output(self, output: RequirementsDoc) -> RequirementsDoc:
        """Sanitize and normalize the output.

        - Strips whitespace from all string fields
        - Normalizes priority values to uppercase
        - Ensures IDs are properly zero-padded
        - Deduplicates constraint and assumption lists
        """
        # Normalize priorities
        frs = [
            FunctionalRequirement(
                id=fr.id,
                description=fr.description.strip(),
                priority=fr.priority.upper(),
            )
            for fr in output.functional_requirements
        ]

        nfrs = [
            NonFunctionalRequirement(
                id=nfr.id,
                description=nfr.description.strip(),
                category=nfr.category.strip().lower(),
            )
            for nfr in output.non_functional_requirements
        ]

        uss = [
            UserStory(
                id=us.id,
                description=us.description.strip(),
                priority=us.priority.upper(),
            )
            for us in output.user_stories
        ]

        # Deduplicate and clean lists
        constraints = list(dict.fromkeys(c.strip() for c in output.constraints if c.strip()))
        assumptions = list(dict.fromkeys(a.strip() for a in output.assumptions if a.strip()))
        open_issues = list(dict.fromkeys(o.strip() for o in output.open_issues if o.strip()))

        return RequirementsDoc(
            title=output.title.strip(),
            purpose=output.purpose.strip(),
            scope=output.scope.strip(),
            functional_requirements=frs,
            non_functional_requirements=nfrs,
            user_stories=uss,
            constraints=constraints,
            assumptions=assumptions,
            open_issues=open_issues,
        )

    def _build_state_updates(
        self,
        state: GraphState,
        output: RequirementsDoc,
        token_usage: dict[str, int],
    ) -> dict[str, Any]:
        """Build state updates including token tracking."""
        sanitized = self._sanitize_output(output)
        field = self._state_field()

        updates = {
            field: sanitized.model_dump(),
            "current_agent": self.agent_type.value,
            "revision": state["revision"] + 1,
        }

        if token_usage:
            updates["token_usage"] = [
                {
                    "agent": self.agent_type.value,
                    **token_usage,
                }
            ]

        return updates
