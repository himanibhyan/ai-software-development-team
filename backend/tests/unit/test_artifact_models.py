from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.models.domain.artifact import (
    ArchitectureArtifact,
    Artifact,
    CodeReviewArtifact,
    DocumentationArtifact,
    RequirementsArtifact,
    SourceCodeArtifact,
    TestSuiteArtifact,
)
from app.models.domain.enums import ArtifactType
from app.models.domain.project import (
    ArchitectureDoc,
    CodeReviewReport,
    ComponentSpec,
    Documentation,
    FunctionalRequirement,
    NonFunctionalRequirement,
    ProjectFile,
    ProjectTree,
    RequirementsDoc,
    ReviewComment,
    TestCase,
    TestSuite,
    UserStory,
)


class TestArtifactBase:
    def test_create_artifact(self):
        pid = uuid4()
        art = Artifact(
            project_id=pid,
            agent_type="requirements",
            artifact_type=ArtifactType.REQUIREMENTS,
            content={"key": "value"},
        )
        assert art.project_id == pid
        assert art.agent_type == "requirements"
        assert art.artifact_type == ArtifactType.REQUIREMENTS
        assert art.content == {"key": "value"}
        assert isinstance(art.id, UUID)
        assert art.revision == 1
        assert art.markdown is None

    def test_artifact_default_revision(self):
        pid = uuid4()
        art = Artifact(
            project_id=pid,
            agent_type="developer",
            artifact_type=ArtifactType.SOURCE_CODE,
            content={"files": []},
        )
        assert art.revision == 1

    def test_artifact_custom_revision(self):
        pid = uuid4()
        art = Artifact(
            project_id=pid,
            agent_type="tester",
            artifact_type=ArtifactType.TEST_SUITE,
            content={},
            revision=3,
        )
        assert art.revision == 3

    def test_artifact_custom_markdown(self):
        pid = uuid4()
        art = Artifact(
            project_id=pid,
            agent_type="docs",
            artifact_type=ArtifactType.DOCUMENTATION,
            content={},
            markdown="# Title",
        )
        assert art.markdown == "# Title"

    def test_artifact_is_frozen(self):
        pid = uuid4()
        art = Artifact(
            project_id=pid,
            agent_type="test",
            artifact_type=ArtifactType.REQUIREMENTS,
            content={},
        )
        with pytest.raises(TypeError):
            art.revision = 5

    def test_artifact_auto_generates_id(self):
        pid = uuid4()
        art = Artifact(
            project_id=pid,
            agent_type="test",
            artifact_type=ArtifactType.ARCHITECTURE,
            content={},
        )
        assert art.id is not None
        assert isinstance(art.id, UUID)


class TestRequirementsArtifact:
    def test_create_requirements_artifact(self):
        pid = uuid4()
        req = RequirementsDoc(
            title="Test Project",
            purpose="Test the artifact model creation",
            scope="Core testing functionality only",
            functional_requirements=[
                FunctionalRequirement(id="FR-01", description="User can log in to the system", priority="P0"),
                FunctionalRequirement(id="FR-02", description="User can log out of the system", priority="P1"),
                FunctionalRequirement(id="FR-03", description="User can view their profile", priority="P1"),
                FunctionalRequirement(id="FR-04", description="User can edit their settings", priority="P2"),
                FunctionalRequirement(id="FR-05", description="Admin can manage all users", priority="P0"),
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(
                    id="NFR-01", description="System must respond quickly to requests", category="performance"
                ),
                NonFunctionalRequirement(
                    id="NFR-02", description="System must protect user data privacy", category="security"
                ),
                NonFunctionalRequirement(
                    id="NFR-03", description="System must handle increased traffic load", category="scalability"
                ),
            ],
            user_stories=[
                UserStory(
                    id="US-01",
                    description="As a registered user, I want to log in securely so that I can access my dashboard",
                    priority="P0",
                ),
                UserStory(
                    id="US-02",
                    description="As a system admin, I want to manage user roles so that I can control access permissions",
                    priority="P1",
                ),
            ],
            constraints=["Must use Python 3.12"],
            assumptions=["Users have internet connectivity"],
        )
        art = RequirementsArtifact(
            project_id=pid,
            agent_type="requirements",
            content=req,
        )
        assert art.artifact_type == ArtifactType.REQUIREMENTS
        assert art.content.title == "Test Project"
        assert len(art.content.functional_requirements) == 5

    def test_requirements_artifact_content_type(self):
        pid = uuid4()
        req = RequirementsDoc(
            title="Test Project",
            purpose="Testing the artifact content type constraint",
            scope="Testing the type constraint enforcement",
            functional_requirements=[
                FunctionalRequirement(
                    id="FR-01", description="First functional requirement description", priority="P0"
                ),
                FunctionalRequirement(
                    id="FR-02", description="Second functional requirement description", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-03", description="Third functional requirement description", priority="P1"
                ),
                FunctionalRequirement(
                    id="FR-04", description="Fourth functional requirement description", priority="P2"
                ),
                FunctionalRequirement(
                    id="FR-05", description="Fifth functional requirement description", priority="P0"
                ),
            ],
            non_functional_requirements=[
                NonFunctionalRequirement(
                    id="NFR-01", description="System must be reliable and available", category="reliability"
                ),
                NonFunctionalRequirement(
                    id="NFR-02", description="System must be easy to use navigate", category="usability"
                ),
                NonFunctionalRequirement(
                    id="NFR-03", description="System must be easy to maintain codebase", category="maintainability"
                ),
            ],
            user_stories=[
                UserStory(
                    id="US-01",
                    description="As a regular user, I want to test the system so that I can verify it works correctly",
                    priority="P0",
                ),
                UserStory(
                    id="US-02",
                    description="As a power user, I want to check all features so that I can confirm they are available",
                    priority="P1",
                ),
            ],
            constraints=["Python"],
            assumptions=["Internet access"],
        )
        art = RequirementsArtifact(
            project_id=pid,
            agent_type="requirements",
            content=req,
        )
        assert isinstance(art.content, RequirementsDoc)


class TestArchitectureArtifact:
    def test_create_architecture_artifact(self):
        pid = uuid4()
        arch = ArchitectureDoc(
            title="System Architecture",
            overview="This document describes the system architecture of the project in detail with all components listed below",
            architecture_pattern="Microservices",
            components=[
                ComponentSpec(
                    name="API Gateway",
                    description="Route incoming requests to the appropriate backend services",
                    technology="FastAPI",
                    responsibilities=["Request routing", "Load balancing"],
                ),
                ComponentSpec(
                    name="Database Layer",
                    description="Store and retrieve persistent application data securely",
                    technology="PostgreSQL",
                    responsibilities=["Data storage", "Query processing"],
                ),
            ],
            data_flow=[
                {"source": "Client", "target": "API Gateway", "protocol": "HTTPS"},
                {"source": "API Gateway", "target": "Service", "protocol": "gRPC"},
            ],
            tech_stack={
                "language": "Python",
                "framework": "FastAPI",
                "database": "PostgreSQL",
            },
            deployment_strategy="Docker containers orchestrated by Kubernetes on AWS ECS for high availability",
            security_considerations=["HTTPS everywhere", "JWT authentication"],
        )
        art = ArchitectureArtifact(
            project_id=pid,
            agent_type="architect",
            content=arch,
        )
        assert art.artifact_type == ArtifactType.ARCHITECTURE
        assert len(art.content.components) == 2


class TestCodeReviewArtifact:
    def test_create_code_review_artifact(self):
        pid = uuid4()
        review = CodeReviewReport(
            summary="Overall the code is well-structured with some minor issues",
            overall_score=8.5,
            comments=[
                ReviewComment(
                    file_path="main.py", line_start=1, line_end=10, severity="info", message="Good structure"
                ),
            ],
            strengths=["Clean code structure", "Good test coverage"],
            weaknesses=["Missing error handling in edge cases"],
            security_concerns=["No input sanitization"],
        )
        art = CodeReviewArtifact(
            project_id=pid,
            agent_type="code_review",
            content=review,
        )
        assert art.artifact_type == ArtifactType.CODE_REVIEW
        assert art.content.overall_score == 8.5


class TestSourceCodeArtifact:
    def test_create_source_code_artifact(self):
        pid = uuid4()
        tree = ProjectTree(
            root="/app",
            files=[
                ProjectFile(path="main.py", content="print('hello')", language="python"),
                ProjectFile(path="utils.py", content="def helper(): pass", language="python"),
            ],
        )
        art = SourceCodeArtifact(
            project_id=pid,
            agent_type="developer",
            content=tree,
        )
        assert art.artifact_type == ArtifactType.SOURCE_CODE
        assert len(art.content.files) == 2


class TestTestSuiteArtifact:
    def test_create_test_suite_artifact(self):
        pid = uuid4()
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(
                    name="test_login",
                    description="Test login functionality",
                    file_path="test_auth.py",
                    code="def test_login(): pass",
                ),
                TestCase(
                    name="test_logout",
                    description="Test logout functionality",
                    file_path="test_auth.py",
                    code="def test_logout(): pass",
                ),
            ],
        )
        art = TestSuiteArtifact(
            project_id=pid,
            agent_type="tester",
            content=suite,
        )
        assert art.artifact_type == ArtifactType.TEST_SUITE
        assert len(art.content.test_cases) == 2


class TestDocumentationArtifact:
    def test_create_documentation_artifact(self):
        pid = uuid4()
        docs = Documentation(
            readme="# Project\nDocumentation for the project",
            setup_guide="1. Install Python\n2. Run pip install",
        )
        art = DocumentationArtifact(
            project_id=pid,
            agent_type="documentation",
            content=docs,
        )
        assert art.artifact_type == ArtifactType.DOCUMENTATION
        assert "Project" in art.content.readme
