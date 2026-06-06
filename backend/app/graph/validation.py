from __future__ import annotations

from typing import Any, Optional

from app.models.domain.enums import AgentType, ProjectStatus
from app.models.domain.project import (
    ArchitectureDoc,
    CodeReviewReport,
    Documentation,
    ProjectTree,
    RequirementsDoc,
    TestSuite,
)

# Schema registry mapping agent types to their output Pydantic models
OUTPUT_SCHEMAS: dict[str, type] = {
    AgentType.REQUIREMENTS.value: RequirementsDoc,
    AgentType.ARCHITECT.value: ArchitectureDoc,
    AgentType.DEVELOPER.value: ProjectTree,
    AgentType.TESTER.value: TestSuite,
    AgentType.CODE_REVIEW.value: CodeReviewReport,
    AgentType.DOCUMENTATION.value: Documentation,
}


def validate_artifact(
    agent_type: str,
    artifact_data: Optional[dict[str, Any]],
) -> list[str]:
    """Validate an artifact against its expected schema.

    Args:
        agent_type: The agent type that produced the artifact.
        artifact_data: The raw dict data to validate.

    Returns:
        A list of validation error messages (empty if valid).
    """
    errors: list[str] = []

    if artifact_data is None:
        return [f"Artifact from {agent_type} is None"]

    schema = OUTPUT_SCHEMAS.get(agent_type)
    if schema is None:
        return [f"No schema registered for agent type: {agent_type}"]

    try:
        schema.model_validate(artifact_data)
    except Exception as e:
        errors.append(f"{agent_type} schema validation failed: {e}")

    # Domain-specific checks
    if agent_type == AgentType.REQUIREMENTS.value:
        frs = artifact_data.get("functional_requirements", [])
        nfrs = artifact_data.get("non_functional_requirements", [])
        uss = artifact_data.get("user_stories", [])
        if len(frs) < 5:
            errors.append(f"Too few functional requirements: {len(frs)} (min 5)")
        if len(nfrs) < 3:
            errors.append(f"Too few non-functional requirements: {len(nfrs)} (min 3)")
        if len(uss) < 2:
            errors.append(f"Too few user stories: {len(uss)} (min 3)")
        if not artifact_data.get("constraints"):
            errors.append("At least one constraint is required")
        if not artifact_data.get("assumptions"):
            errors.append("At least one assumption is required")
        # Validate sub-field structure
        for i, fr in enumerate(frs):
            if not isinstance(fr, dict) or "id" not in fr or "description" not in fr:
                errors.append(f"Functional requirement at index {i} is missing 'id' or 'description'")
        for i, nfr in enumerate(nfrs):
            if not isinstance(nfr, dict) or "id" not in nfr or "description" not in nfr or "category" not in nfr:
                errors.append(f"Non-functional requirement at index {i} is missing required fields")
        for i, us in enumerate(uss):
            if not isinstance(us, dict) or "id" not in us or "description" not in us:
                errors.append(f"User story at index {i} is missing 'id' or 'description'")

    elif agent_type == AgentType.ARCHITECT.value:
        components = artifact_data.get("components", [])
        if len(components) < 3:
            errors.append(f"Too few components: {len(components)} (min 3)")
        for i, comp in enumerate(components):
            if not isinstance(comp, dict):
                errors.append(f"Component at index {i} is not a dict")
                continue
            if "name" not in comp or "description" not in comp or "technology" not in comp:
                errors.append(f"Component at index {i} missing required fields (name, description, technology)")
            if "responsibilities" not in comp or not comp.get("responsibilities"):
                errors.append(f"Component '{comp.get('name', '?')}' has no responsibilities")
        tech_stack = artifact_data.get("tech_stack", {})
        if len(tech_stack) < 5:
            errors.append(f"Too few tech stack entries: {len(tech_stack)} (min 5)")
        data_flow = artifact_data.get("data_flow", [])
        if len(data_flow) < 4:
            errors.append(f"Too few data flow steps: {len(data_flow)} (min 4)")
        security = artifact_data.get("security_considerations", [])
        if len(security) < 3:
            errors.append(f"Too few security considerations: {len(security)} (min 3)")
        deployment = artifact_data.get("deployment_strategy", "")
        if len(deployment) < 20:
            errors.append("Deployment strategy too short (min 20 chars)")
        db_design = artifact_data.get("database_design")
        if db_design:
            tables = db_design.get("tables", [])
            if len(tables) < 2:
                errors.append(f"Too few database tables: {len(tables)} (min 2)")
            for ti, table in enumerate(tables):
                cols = table.get("columns", [])
                if len(cols) < 2:
                    errors.append(f"Table '{table.get('name', f'idx_{ti}')}' has too few columns: {len(cols)} (min 2)")
                has_pk = any(
                    "primary" in str(col.get("constraints", "")).lower()
                    for col in cols
                )
                if not has_pk:
                    errors.append(f"Table '{table.get('name', f'idx_{ti}')}' has no primary key")
        api_spec = artifact_data.get("api_spec")
        if api_spec:
            endpoints = api_spec.get("endpoints", [])
            if len(endpoints) < 3:
                errors.append(f"Too few API endpoints: {len(endpoints)} (min 3)")

    elif agent_type == AgentType.DEVELOPER.value:
        files = artifact_data.get("files", [])
        if not files:
            errors.append("No files generated")
        elif not any("main" in f.get("path", "") for f in files):
            errors.append("No main entry point found")

    elif agent_type == AgentType.TESTER.value:
        test_cases = artifact_data.get("test_cases", [])
        if not test_cases:
            errors.append("No test cases generated")

    elif agent_type == AgentType.CODE_REVIEW.value:
        score = artifact_data.get("overall_score", 0)
        if score < 0 or score > 10:
            errors.append(f"Score out of range: {score}")

    elif agent_type == AgentType.DOCUMENTATION.value:
        if not artifact_data.get("readme"):
            errors.append("README is missing")

    return errors


def validate_artifact_required_fields(
    agent_type: str,
    artifact_data: Optional[dict[str, Any]],
) -> list[str]:
    """Check that all required fields are present in the artifact."""
    errors: list[str] = []

    if artifact_data is None:
        return [f"Artifact from {agent_type} is None"]

    schema = OUTPUT_SCHEMAS.get(agent_type)
    if schema is None:
        return []

    for field_name, field_info in schema.model_fields.items():
        if field_info.is_required():
            if field_name not in artifact_data:
                errors.append(f"Missing required field '{field_name}' in {agent_type} output")
            elif artifact_data[field_name] is None:
                errors.append(f"Required field '{field_name}' is None in {agent_type} output")

    return errors


def is_valid_state_transition(
    current_status: str,
    target_agent: str,
) -> bool:
    """Check if the state transition is valid.

    Valid transitions:
      pending → requirements
      requirements → architecture
      architecture → development
      development → code_review
      code_review → tester  (if score acceptable)
      code_review → development (if score below threshold)
      tester → documentation
      documentation → completed
    """
    valid_transitions = {
        "pending": ["requirements"],
        "running": ["requirements", "architecture", "development", "code_review", "tester", "documentation"],
    }
    return target_agent in valid_transitions.get(current_status, [])
