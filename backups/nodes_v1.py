from __future__ import annotations

from app.agents.registry import registry as agent_registry
from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.graph.state import GraphState
from app.graph.validation import validate_artifact

logger = get_logger(__name__)


def _get_registry():
    if agent_registry is None:
        raise AppException("Agent registry not initialized. Call init_registry() during startup.")
    return agent_registry


async def requirements_node(state: GraphState) -> dict:
    """Node: Requirements Agent — produces the SRS document."""
    logger.info("node:requirements_agent", project_id=state["project_id"])
    agent = _get_registry().get_agent("requirements")

    try:
        updates = await agent.process(state)
        errors = validate_artifact("requirements", updates.get("requirements"))
        if errors:
            logger.warning("requirements_validation_issues", errors=errors)
        updates["completed_steps"] = ["requirements"]
        return updates
    except Exception as e:
        logger.error("requirements_node_failed", error=str(e))
        return _error_updates(state, "requirements", str(e))


async def architect_node(state: GraphState) -> dict:
    """Node: Architect Agent — produces the architecture design."""
    logger.info("node:architect_agent", project_id=state["project_id"])
    agent = _get_registry().get_agent("architect")

    try:
        updates = await agent.process(state)
        errors = validate_artifact("architect", updates.get("architecture"))
        if errors:
            logger.warning("architecture_validation_issues", errors=errors)
        updates["completed_steps"] = ["architecture"]
        return updates
    except Exception as e:
        logger.error("architect_node_failed", error=str(e))
        return _error_updates(state, "architecture", str(e))


async def developer_node(state: GraphState) -> dict:
    """Node: Developer Agent — produces source code.

    If this is a rework iteration (triggered by code review),
    the existing review_report is passed as context so the
    developer can address specific feedback.
    """
    logger.info(
        "node:developer_agent",
        project_id=state["project_id"],
        rework=state.get("review_report") is not None,
    )
    agent = _get_registry().get_agent("developer")

    try:
        updates = await agent.process(state)
        errors = validate_artifact("developer", updates.get("source_code"))
        if errors:
            logger.warning("developer_validation_issues", errors=errors)
        if "completed_steps" not in updates:
            updates["completed_steps"] = ["development"]
        return updates
    except Exception as e:
        logger.error("developer_node_failed", error=str(e))
        return _error_updates(state, "development", str(e))


async def code_review_node(state: GraphState) -> dict:
    """Node: Code Review Agent — reviews source code quality.

    Increments review_attempts counter. Routes to developer
    if score is below threshold in the edge function.
    """
    logger.info(
        "node:code_review_agent",
        project_id=state["project_id"],
        attempt=state.get("review_attempts", 0) + 1,
    )
    agent = _get_registry().get_agent("code_review")

    try:
        updates = await agent.process(state)
        errors = validate_artifact("code_review", updates.get("review_report"))
        if errors:
            logger.warning("code_review_validation_issues", errors=errors)
        updates["review_attempts"] = state.get("review_attempts", 0) + 1
        updates["completed_steps"] = ["code_review"]
        return updates
    except Exception as e:
        logger.error("code_review_node_failed", error=str(e))
        return _error_updates(state, "code_review", str(e))


async def tester_node(state: GraphState) -> dict:
    """Node: Tester Agent — produces test suite."""
    logger.info("node:tester_agent", project_id=state["project_id"])
    agent = _get_registry().get_agent("tester")

    try:
        updates = await agent.process(state)
        errors = validate_artifact("tester", updates.get("test_suite"))
        if errors:
            logger.warning("tester_validation_issues", errors=errors)
        updates["completed_steps"] = ["testing"]
        return updates
    except Exception as e:
        logger.error("tester_node_failed", error=str(e))
        return _error_updates(state, "testing", str(e))


async def documentation_node(state: GraphState) -> dict:
    """Node: Documentation Agent — produces technical documentation."""
    logger.info("node:documentation_agent", project_id=state["project_id"])
    agent = _get_registry().get_agent("documentation")

    try:
        updates = await agent.process(state)
        errors = validate_artifact("documentation", updates.get("documentation"))
        if errors:
            logger.warning("documentation_validation_issues", errors=errors)
        updates["completed_steps"] = ["documentation"]
        return updates
    except Exception as e:
        logger.error("documentation_node_failed", error=str(e))
        return _error_updates(state, "documentation", str(e))


async def validate_input_node(state: GraphState) -> dict:
    """Node: Validate the initial input before pipeline execution."""
    logger.info("node:validate_input", project_id=state["project_id"])

    if not state["idea"] or len(state["idea"].strip()) < 10:
        error_msg = "Input idea must be at least 10 characters"
        logger.error("input_validation_failed", error=error_msg)
        return {
            "status": "failed",
            "errors": [{"agent": "validator", "message": error_msg}],
            "revision": state["revision"] + 1,
        }

    # Mark requirements as the next pending step
    return {
        "status": "running",
        "revision": state["revision"] + 1,
    }


async def persistence_node(state: GraphState) -> dict:
    """Node: Final state — persist artifacts and mark complete."""
    from datetime import datetime, timezone

    logger.info("node:persistence", project_id=state["project_id"])

    summary = {
        "agent": "persistence",
        "artifacts": {
            k: v is not None
            for k, v in state.items()
            if k in ("requirements", "architecture", "source_code", "test_suite", "documentation", "review_report")
        },
        "total_tokens": sum(
            t.get("total_tokens", 0) for t in state.get("token_usage", [])
        ),
    }

    return {
        "status": "completed",
        "end_time": datetime.now(timezone.utc).isoformat(),
        "current_agent": None,
        "agent_results": [summary],
        "revision": state["revision"] + 1,
    }


async def error_node(state: GraphState) -> dict:
    """Node: Handle unrecoverable pipeline errors."""
    from datetime import datetime, timezone

    logger.error(
        "node:error_handler",
        project_id=state["project_id"],
        errors=state["errors"],
    )

    return {
        "status": "failed",
        "end_time": datetime.now(timezone.utc).isoformat(),
        "current_agent": None,
        "revision": state["revision"] + 1,
    }


def _error_updates(state: GraphState, step: str, error_msg: str) -> dict:
    """Build error state updates for a failed node."""
    return {
        "errors": [{"step": step, "message": error_msg, "agent": state.get("current_agent")}],
        "status": "failed",
        "current_agent": None,
        "revision": state["revision"] + 1,
    }
