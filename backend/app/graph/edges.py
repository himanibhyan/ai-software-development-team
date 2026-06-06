from __future__ import annotations

from app.core.logging import get_logger
from app.graph.state import GraphState

logger = get_logger(__name__)


def route_after_validation(state: GraphState) -> str:
    """Route to requirements agent, or fail if validation failed."""
    if state["status"] == "failed":
        logger.warning("input_validation_failed, routing to error_handler")
        return "error_handler"
    return "requirements_agent"


def route_after_requirements(state: GraphState) -> str:
    """Route to architect agent, or fail if requirements could not be generated."""
    if state.get("requirements") is None:
        logger.error("requirements_generation_failed", project_id=state["project_id"])
        return "error_handler"
    return "architect_agent"


def route_after_architecture(state: GraphState) -> str:
    """Route to developer agent, or fail if architecture could not be designed."""
    if state.get("architecture") is None:
        logger.error("architecture_generation_failed", project_id=state["project_id"])
        return "error_handler"
    return "developer_agent"


def route_after_development(state: GraphState) -> str:
    """Route to code review after development."""
    if state.get("source_code") is None:
        logger.error("code_generation_failed", project_id=state["project_id"])
        return "error_handler"
    return "code_review_agent"


def route_after_code_review(state: GraphState) -> str:
    """Route based on code review outcome.

    - If review score >= threshold or max attempts reached → proceed to tester
    - If review score < threshold and attempts remain → rework via developer
    - If code is missing → error
    """
    if state.get("source_code") is None:
        return "error_handler"

    review = state.get("review_report")
    if review is None:
        # No review generated yet — proceed to tester anyway
        logger.info("no_review_available, proceeding to tester")
        return "tester_agent"

    score = review.get("overall_score", 10.0)
    attempts = state.get("review_attempts", 0)
    max_attempts = state.get("max_review_attempts", 3)

    if score >= 6.0:
        logger.info(
            "code_review_passed",
            score=score,
            project_id=state["project_id"],
        )
        return "tester_agent"

    if attempts < max_attempts:
        logger.info(
            "code_review_below_threshold, reworking",
            score=score,
            attempt=attempts,
            max_attempts=max_attempts,
            project_id=state["project_id"],
        )
        return "developer_agent"

    logger.warning(
        "code_review_max_attempts_reached, proceeding despite low score",
        score=score,
        attempts=attempts,
        project_id=state["project_id"],
    )
    return "tester_agent"


def route_after_testing(state: GraphState) -> str:
    """Route to documentation agent, or fail if tests could not be generated."""
    if state.get("test_suite") is None:
        logger.error("test_generation_failed", project_id=state["project_id"])
        return "error_handler"
    return "documentation_agent"


def route_after_documentation(state: GraphState) -> str:
    """Route to persistence/final node, or fail if docs could not be generated."""
    if state.get("documentation") is None:
        logger.warning(
            "documentation_generation_returned_none, proceeding to finalize anyway",
            project_id=state["project_id"],
        )
    return "persistence_node"


def should_continue(state: GraphState) -> str:
    """Top-level router: check if pipeline should continue or stop.

    This is called at the start of each step to check for failure state.
    """
    if state["status"] in ("failed", "completed"):
        logger.info(
            "pipeline_terminated",
            status=state["status"],
            project_id=state["project_id"],
        )
        return "end"
    return "continue"
