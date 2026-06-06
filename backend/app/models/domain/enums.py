from __future__ import annotations

from enum import StrEnum, auto


class AgentType(StrEnum):
    REQUIREMENTS = "requirements"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    CODE_REVIEW = "code_review"
    DOCUMENTATION = "documentation"
    ORCHESTRATOR = "orchestrator"


class ProjectStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REFINING = "refining"


class AgentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ArtifactType(StrEnum):
    REQUIREMENTS = auto()
    ARCHITECTURE = auto()
    SOURCE_CODE = auto()
    TEST_SUITE = auto()
    DOCUMENTATION = auto()
    CODE_REVIEW = auto()
