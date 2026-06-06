from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
    constraints: Optional[dict[str, Any]] = None
    status: str
    requirements: Optional[dict[str, Any]] = None
    architecture: Optional[dict[str, Any]] = None
    source_code: Optional[dict[str, Any]] = None
    test_suite: Optional[dict[str, Any]] = None
    documentation: Optional[dict[str, Any]] = None
    review_report: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


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
    error: Optional[str] = None


class CreateProjectResponse(BaseModel):
    project_id: UUID
    status: str
    status_url: str


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
    errors: Optional[list[dict[str, Any]]] = None
