from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.domain.enums import AgentStatus, ProjectStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FunctionalRequirement(BaseModel):
    id: str = Field(pattern=r"^FR-\d{2,}$")
    description: str = Field(min_length=10)
    priority: str = Field(default="P0", pattern=r"^P[0-2]$")


class NonFunctionalRequirement(BaseModel):
    id: str = Field(pattern=r"^NFR-\d{2,}$")
    description: str = Field(min_length=10)
    category: str = Field(
        default="performance",
        pattern=r"^(performance|security|usability|reliability|scalability|maintainability|availability)$",
    )


class UserStory(BaseModel):
    id: str = Field(pattern=r"^US-\d{2,}$")
    description: str = Field(
        min_length=15,
        description="Must follow: 'As a [role], I want [action] so that [benefit]'",
    )
    priority: str = Field(default="P0", pattern=r"^P[0-2]$")


class RequirementsDoc(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    purpose: str = Field(min_length=20, max_length=2000)
    scope: str = Field(min_length=20, max_length=2000)
    functional_requirements: list[FunctionalRequirement] = Field(min_length=5)
    non_functional_requirements: list[NonFunctionalRequirement] = Field(min_length=3)
    user_stories: list[UserStory] = Field(min_length=2)
    constraints: list[str] = Field(min_length=1)
    assumptions: list[str] = Field(min_length=1)
    open_issues: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class ComponentSpec(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=10)
    technology: str = Field(min_length=1)
    responsibilities: list[str] = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    api_endpoints: list[dict[str, str]] = Field(default_factory=list)

    model_config = {"frozen": True}


class DatabaseTable(BaseModel):
    name: str = Field(min_length=1)
    columns: list[dict[str, str]] = Field(min_length=1, description="List of {name, type, constraints} objects")
    description: str = Field(min_length=5)
    relationships: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}


class DatabaseDesign(BaseModel):
    engine: str = Field(min_length=1, description="e.g., PostgreSQL 16, MySQL 8")
    tables: list[DatabaseTable] = Field(min_length=1)
    orm: Optional[str] = Field(None, description="e.g., SQLAlchemy 2.0, Prisma, Drizzle")
    migration_tool: Optional[str] = Field(None, description="e.g., Alembic, Prisma Migrate")
    caching_strategy: Optional[str] = Field(None, description="e.g., Redis caching with cache-aside pattern")
    sharding_strategy: Optional[str] = Field(None, description="If applicable")
    backup_strategy: Optional[str] = Field(None, description="e.g., Daily snapshots + WAL archiving")

    model_config = {"frozen": True}


class APIEndpoint(BaseModel):
    path: str = Field(min_length=1, pattern=r"^/")
    method: str = Field(pattern=r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$")
    description: str = Field(min_length=5)
    request_body: Optional[dict[str, Any]] = Field(None, description="JSON schema of request body")
    response_body: Optional[dict[str, Any]] = Field(None, description="JSON schema of response body")
    auth_required: bool = Field(default=True)
    rate_limited: bool = Field(default=False)

    model_config = {"frozen": True}


class APISpec(BaseModel):
    protocol: str = Field(default="REST", pattern=r"^(REST|GraphQL|gRPC|WebSocket|SOAP)$")
    base_url: str = Field(min_length=1, description="e.g., /api/v1")
    endpoints: list[APIEndpoint] = Field(min_length=1)
    auth_method: str = Field(default="JWT", description="e.g., JWT, OAuth 2.0, API keys, Session")
    rate_limiting: Optional[str] = Field(None, description="e.g., 1000 req/min per user")
    versioning_strategy: Optional[str] = Field(None, description="e.g., URL path versioning /v1/, /v2/")

    model_config = {"frozen": True}


class FolderEntry(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(pattern=r"^(file|directory)$")
    children: list[FolderEntry] = Field(default_factory=list)
    description: Optional[str] = Field(None)

    model_config = {"frozen": True}


class FolderStructure(BaseModel):
    root: str = Field(min_length=1)
    entries: list[FolderEntry] = Field(min_length=1)
    description: str = Field(default="Project folder structure")

    model_config = {"frozen": True}


class ArchitectureDoc(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    overview: str = Field(min_length=20, max_length=3000)
    architecture_pattern: str = Field(
        min_length=1,
        description="e.g., Microservices, Layered, Event-Driven, Hexagonal, CQRS, Serverless",
    )
    components: list[ComponentSpec] = Field(min_length=2)
    data_flow: list[dict[str, str]] = Field(
        min_length=2,
        description="Sequence of steps showing how data moves through the system",
    )
    tech_stack: dict[str, str] = Field(
        min_length=3,
        description="Technology choices keyed by category: language, framework, database, messaging, cache, etc.",
    )
    diagram_mermaid: Optional[str] = Field(None, description="Mermaid.js diagram definition string")
    deployment_strategy: str = Field(min_length=20, description="How the system is deployed and scaled")
    security_considerations: list[str] = Field(min_length=1)
    database_design: Optional[DatabaseDesign] = Field(None, description="Database schema design")
    api_spec: Optional[APISpec] = Field(None, description="API specification")
    folder_structure: Optional[FolderStructure] = Field(None, description="Recommended project folder structure")
    scalability_notes: Optional[str] = Field(None, description="Horizontal/vertical scaling approach")
    monitoring_strategy: Optional[str] = Field(None, description="Logging, metrics, alerting approach")

    model_config = {"frozen": True}


class ProjectFile(BaseModel):
    path: str
    content: str
    language: str

    model_config = {"frozen": True}


class ProjectTree(BaseModel):
    root: str
    files: list[ProjectFile]
    dependency_files: list[str] = []

    model_config = {"frozen": True}


class TestCase(BaseModel):
    name: str
    description: str
    file_path: str
    code: str
    type: str = "unit"

    model_config = {"frozen": True}


class TestSuite(BaseModel):
    test_framework: str
    test_config: dict[str, Any] = {}
    test_cases: list[TestCase]
    coverage_target: float = 0.8

    model_config = {"frozen": True}


class ReviewComment(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    severity: str = "info"
    message: str
    suggestion: Optional[str] = None

    model_config = {"frozen": True}


class CodeReviewReport(BaseModel):
    summary: str
    overall_score: float = Field(ge=0.0, le=10.0)
    comments: list[ReviewComment]
    strengths: list[str]
    weaknesses: list[str]
    security_concerns: list[str]

    model_config = {"frozen": True}


class Documentation(BaseModel):
    readme: str
    api_docs: Optional[str] = None
    setup_guide: str
    architecture_overview: Optional[str] = None
    contributing_guide: Optional[str] = None

    model_config = {"frozen": True}


class AgentError(BaseModel):
    agent_type: str
    message: str
    details: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=_utcnow)


class AgentExecution(BaseModel):
    agent_type: str
    status: AgentStatus = AgentStatus.PENDING
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    error: Optional[AgentError] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class ProjectIdeation(BaseModel):
    idea: str
    constraints: Optional[dict[str, Any]] = None
    project_id: UUID = Field(default_factory=uuid4)
    status: ProjectStatus = ProjectStatus.PENDING
    created_at: datetime = Field(default_factory=_utcnow)
