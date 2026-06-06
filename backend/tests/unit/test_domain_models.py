from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.models.domain.project import (
    APISpec,
    APIEndpoint,
    CodeReviewReport,
    ComponentSpec,
    DatabaseDesign,
    DatabaseTable,
    Documentation,
    FolderEntry,
    FolderStructure,
    ProjectFile,
    ProjectTree,
    RequirementsDoc,
    ReviewComment,
    TestCase,
    TestSuite,
)


class TestRequirementsDoc:
    def test_valid_requirements(self):
        doc = RequirementsDoc(
            title="Test Project",
            purpose="Testing",
            scope="Full stack",
            functional_requirements=[{"id": "FR-01", "description": "User login"}],
            non_functional_requirements=[{"id": "NFR-01", "description": "Fast"}],
            user_stories=[{"id": "US-01", "description": "As a user..."}],
            constraints=["Must use Python"],
            assumptions=["Internet available"],
            open_issues=["Data model"],
        )
        assert doc.title == "Test Project"
        assert len(doc.functional_requirements) == 1

    def test_requirements_doc_is_frozen(self):
        doc = RequirementsDoc(
            title="Test",
            purpose="Test",
            scope="Test",
            functional_requirements=[],
            non_functional_requirements=[],
            user_stories=[],
            constraints=[],
            assumptions=[],
            open_issues=[],
        )
        with pytest.raises(ValidationError):
            doc.title = "New Title"


class TestComponentSpec:
    def test_valid_component(self):
        component = ComponentSpec(
            name="Auth Service",
            description="Handles authentication",
            technology="FastAPI",
            responsibilities=["Login", "Register"],
            dependencies=["Database"],
            api_endpoints=[{"path": "/login", "method": "POST"}],
        )
        assert component.name == "Auth Service"

    def test_invalid_component_empty_name(self):
        with pytest.raises(ValidationError):
            ComponentSpec(
                name="",
                description="Short",
                technology="Python",
                responsibilities=["Do"],
            )


class TestDatabaseDesign:
    def test_valid_database_design(self):
        design = DatabaseDesign(
            engine="PostgreSQL 16",
            tables=[
                DatabaseTable(
                    name="users",
                    columns=[
                        {"name": "id", "type": "UUID", "constraints": "PRIMARY KEY"},
                        {"name": "email", "type": "VARCHAR", "constraints": "UNIQUE NOT NULL"},
                    ],
                    description="User accounts",
                ),
            ],
            orm="SQLAlchemy 2.0",
            migration_tool="Alembic",
        )
        assert design.engine == "PostgreSQL 16"
        assert len(design.tables) == 1
        assert design.tables[0].name == "users"

    def test_database_table_requires_columns(self):
        with pytest.raises(ValidationError):
            DatabaseTable(
                name="empty",
                columns=[],
                description="No columns",
            )


class TestAPISpec:
    def test_valid_api_spec(self):
        spec = APISpec(
            protocol="REST",
            base_url="/api/v1",
            endpoints=[
                APIEndpoint(path="/login", method="POST", description="User login", auth_required=False),
                APIEndpoint(path="/users", method="GET", description="List users", auth_required=True),
                APIEndpoint(path="/users/{id}", method="GET", description="Get user", auth_required=True),
            ],
            auth_method="JWT",
        )
        assert spec.protocol == "REST"
        assert len(spec.endpoints) == 3

    def test_invalid_method(self):
        with pytest.raises(ValidationError):
            APIEndpoint(path="/test", method="INVALID", description="Bad method")

    def test_path_must_start_with_slash(self):
        with pytest.raises(ValidationError):
            APIEndpoint(path="api/login", method="GET", description="Missing slash")


class TestFolderStructure:
    def test_valid_folder_structure(self):
        fs = FolderStructure(
            root="myproject",
            entries=[
                FolderEntry(name="src", type="directory", children=[
                    FolderEntry(name="main.py", type="file", description="Entry point"),
                ]),
                FolderEntry(name="README.md", type="file"),
            ],
        )
        assert fs.root == "myproject"
        assert len(fs.entries) == 2

    def test_invalid_entry_type(self):
        with pytest.raises(ValidationError):
            FolderEntry(name="x", type="symlink")


class TestProjectTree:
    def test_valid_project_tree(self):
        tree = ProjectTree(
            root="my_project",
            files=[
                ProjectFile(
                    path="main.py",
                    content="print('hello')",
                    language="python",
                )
            ],
        )
        assert len(tree.files) == 1
        assert tree.files[0].path == "main.py"


class TestTestSuite:
    def test_valid_test_suite(self):
        suite = TestSuite(
            test_framework="pytest",
            test_cases=[
                TestCase(
                    name="test_login",
                    description="Tests user login",
                    file_path="tests/test_auth.py",
                    code="def test_login(): pass",
                )
            ],
        )
        assert suite.test_framework == "pytest"
        assert len(suite.test_cases) == 1


class TestCodeReviewReport:
    def test_valid_review(self):
        report = CodeReviewReport(
            summary="Good code overall",
            overall_score=8.5,
            comments=[
                ReviewComment(
                    file_path="main.py",
                    line_start=10,
                    line_end=12,
                    severity="warning",
                    message="Unused variable",
                )
            ],
            strengths=["Clean code"],
            weaknesses=["Missing tests"],
            security_concerns=["SQL injection"],
        )
        assert report.overall_score == 8.5
        assert len(report.comments) == 1

    def test_invalid_score_high(self):
        with pytest.raises(ValidationError):
            CodeReviewReport(
                summary="Bad",
                overall_score=15.0,
                comments=[],
                strengths=[],
                weaknesses=[],
                security_concerns=[],
            )


class TestDocumentation:
    def test_valid_docs(self):
        docs = Documentation(
            readme="# Project",
            setup_guide="pip install",
            api_docs="## API",
        )
        assert docs.readme == "# Project"
