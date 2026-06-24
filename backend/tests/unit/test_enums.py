from __future__ import annotations

from app.models.domain.enums import AgentType, ArtifactType, ProjectStatus


class TestEnums:
    def test_agent_types(self):
        assert AgentType.REQUIREMENTS.value == "requirements"
        assert AgentType.ARCHITECT.value == "architect"
        assert AgentType.DEVELOPER.value == "developer"
        assert AgentType.TESTER.value == "tester"
        assert AgentType.CODE_REVIEW.value == "code_review"
        assert AgentType.DOCUMENTATION.value == "documentation"
        assert AgentType.ORCHESTRATOR.value == "orchestrator"

    def test_project_status_values(self):
        assert ProjectStatus.PENDING.value == "pending"
        assert ProjectStatus.RUNNING.value == "running"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.FAILED.value == "failed"
        assert ProjectStatus.REFINING.value == "refining"

    def test_artifact_type_values(self):
        assert ArtifactType.REQUIREMENTS.value == "requirements"
        assert ArtifactType.ARCHITECTURE.value == "architecture"
        assert ArtifactType.SOURCE_CODE.value == "source_code"
        assert ArtifactType.TEST_SUITE.value == "test_suite"
        assert ArtifactType.DOCUMENTATION.value == "documentation"
        assert ArtifactType.CODE_REVIEW.value == "code_review"
