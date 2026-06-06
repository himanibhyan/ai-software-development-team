from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    idea: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Natural language description of the software idea",
    )
    constraints: Optional[dict[str, Any]] = Field(
        None,
        description="Optional constraints (tech stack, preferences, etc.)",
    )


class RefineProjectRequest(BaseModel):
    feedback: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="User feedback to refine the generated project",
    )
    target_agents: Optional[list[str]] = Field(
        None,
        description="Specific agents to re-run (default: all)",
    )


class ExportProjectRequest(BaseModel):
    repository_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="GitHub repository name",
    )
    organization: Optional[str] = Field(
        None,
        description="GitHub organization (defaults to personal account)",
    )
    private: bool = Field(False, description="Create private repository")
