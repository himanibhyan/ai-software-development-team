from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ProjectSummaryResponse(BaseModel):
    id: UUID
    idea: str
    status: str
    created_at: datetime
    updated_at: datetime
    artifact_count: int = 0

    model_config = {"from_attributes": True}


class ProjectDetailResponse(BaseModel):
    id: UUID
    idea: str
    constraints: dict[str, Any] | None = None
    status: str
    requirements: dict[str, Any] | None = None
    architecture: dict[str, Any] | None = None
    source_code: dict[str, Any] | None = None
    test_suite: dict[str, Any] | None = None
    documentation: dict[str, Any] | None = None
    review_report: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class AgentStatusResponse(BaseModel):
    project_id: UUID
    agent_type: str
    status: str
    duration_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None


class CreateProjectResponse(BaseModel):
    project_id: UUID
    status: str
    status_url: str


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    errors: list[dict[str, Any]] | None = None
