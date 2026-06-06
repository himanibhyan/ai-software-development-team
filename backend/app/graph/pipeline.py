from __future__ import annotations

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from app.core.logging import get_logger
from app.graph.edges import (
    route_after_code_review,
    route_after_documentation,
    route_after_development,
    route_after_requirements,
    route_after_architecture,
    route_after_testing,
    route_after_validation,
)
from app.graph.nodes import (
    architect_node,
    code_review_node,
    developer_node,
    documentation_node,
    error_node,
    persistence_node,
    requirements_node,
    tester_node,
    validate_input_node,
)
from app.graph.state import GraphState, state_summary

logger = get_logger(__name__)


def build_pipeline() -> StateGraph:
    """Construct the LangGraph StateGraph pipeline.

    The pipeline follows a sequential agent workflow with a feedback loop:

    ```
    START
      │
      ▼
    validate_input ──(failed)──▶ error_handler ──▶ END
      │
      ▼
    requirements_agent ──(failed)──▶ error_handler ──▶ END
      │
      ▼
    architect_agent ──(failed)──▶ error_handler ──▶ END
      │
      ▼
    developer_agent ──(failed)──▶ error_handler ──▶ END
      │
      ▼
    code_review_agent
      │
      ├──(score ≥ 6.0 OR max attempts)──▶ tester_agent
      │                                       │
      └──(score < 6.0 AND attempts remain)──▶ developer_agent (rework loop)
                                              │
                                              ▼
                                            tester_agent ──(failed)──▶ error_handler
                                              │
                                              ▼
                                            documentation_agent
                                              │
                                              ▼
                                            persistence_node ──▶ END
    ```

    Error Handling:
    - Every node is wrapped in try/except in nodes.py
    - Errors route to the central error_handler node
    - The error_handler marks the project as failed and terminates
    - Agent-level retries (2 retries) happen *inside* each agent via BaseAgent.process()
    - Network/API failures use tenacity exponential backoff in LLMService

    Code Review Feedback Loop:
    - After code review, if overall_score < 6.0 and attempts < max_attempts,
      the pipeline routes back to the developer with review context
    - The developer re-generates code addressing the review feedback
    - After max_attempts reached, proceeds to tester regardless of score

    State Transitions:
    - Each node returns a dict of field updates
    - LangGraph merges updates into shared state using reducers
    - errors/agent_results/token_usage use ``operator.add`` (appends)
    - All other fields are overwritten on each update
    """

    workflow = StateGraph(GraphState)

    # ── Register all nodes ──────────────────────────────────
    workflow.add_node("validate_input", validate_input_node)
    workflow.add_node("requirements_agent", requirements_node)
    workflow.add_node("architect_agent", architect_node)
    workflow.add_node("developer_agent", developer_node)
    workflow.add_node("code_review_agent", code_review_node)
    workflow.add_node("tester_agent", tester_node)
    workflow.add_node("documentation_agent", documentation_node)
    workflow.add_node("persistence_node", persistence_node)
    workflow.add_node("error_handler", error_node)

    # ── Define edges ────────────────────────────────────────
    workflow.set_entry_point("validate_input")

    # validate_input → requirements_agent OR error_handler
    workflow.add_conditional_edges(
        "validate_input",
        route_after_validation,
    )

    # Sequential agent chain
    # Each router returns the next node name or "error_handler"
    workflow.add_conditional_edges("requirements_agent", route_after_requirements)
    workflow.add_conditional_edges("architect_agent", route_after_architecture)
    workflow.add_conditional_edges("developer_agent", route_after_development)

    # Code review → developer (rework) OR tester OR error_handler
    workflow.add_conditional_edges("code_review_agent", route_after_code_review)

    # Tester → documentation OR error_handler
    workflow.add_conditional_edges("tester_agent", route_after_testing)

    # Documentation → persistence OR error_handler
    workflow.add_conditional_edges("documentation_agent", route_after_documentation)

    # Terminal edges
    workflow.add_edge("persistence_node", END)
    workflow.add_edge("error_handler", END)

    # ── Compile with checkpointing ──────────────────────────
    memory = MemorySaver()
    pipeline = workflow.compile(checkpointer=memory)

    logger.info("pipeline_compiled", nodes=list(workflow.nodes.keys()))
    return pipeline


# Pre-compiled singleton
_pipeline_instance: StateGraph | None = None


def get_pipeline() -> StateGraph:
    """Get or create the pipeline singleton."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = build_pipeline()
    return _pipeline_instance
