from __future__ import annotations

from app.graph.validation import validate_artifact


class TestValidateArtifact:
    def test_none_artifact_returns_error(self):
        errors = validate_artifact("requirements", None)
        assert len(errors) == 1
        assert "None" in errors[0]

    def test_invalid_agent_type_returns_error(self):
        errors = validate_artifact("unknown_agent", {"foo": "bar"})
        assert len(errors) == 1
        assert "No schema registered" in errors[0]

    def test_valid_requirements_passes(self):
        data = {
            "title": "Test",
            "purpose": "Testing",
            "scope": "Full",
            "functional_requirements": [{"id": "FR-01", "description": "Login"} for _ in range(5)],
            "non_functional_requirements": [{"id": "NFR-01", "description": "Fast"} for _ in range(3)],
            "user_stories": [{"id": "US-01", "description": "As a user..."}],
            "constraints": [],
            "assumptions": [],
            "open_issues": [],
        }
        errors = validate_artifact("requirements", data)
        assert errors == []

    def test_requirements_too_few_frs(self):
        data = {
            "title": "Test",
            "purpose": "Testing",
            "scope": "Full",
            "functional_requirements": [{"id": "FR-01", "description": "Login"}],
            "non_functional_requirements": [{"id": "NFR-01", "description": "Fast"} for _ in range(3)],
            "user_stories": [],
            "constraints": [],
            "assumptions": [],
            "open_issues": [],
        }
        errors = validate_artifact("requirements", data)
        assert any("Too few functional requirements" in e for e in errors)

    def test_architecture_too_few_components(self):
        data = {
            "title": "Arch",
            "overview": "Overview",
            "architecture_pattern": "Layered",
            "components": [
                {"name": "API", "description": "API layer", "technology": "FastAPI", "responsibilities": ["Route"], "dependencies": []},
                {"name": "Service", "description": "Service layer", "technology": "Python", "responsibilities": ["Process"], "dependencies": []},
            ],
            "data_flow": [{"step": "1", "description": "Request"}, {"step": "2", "description": "Process"}, {"step": "3", "description": "Response"}, {"step": "4", "description": "Done"}],
            "tech_stack": {"lang": "Python", "framework": "FastAPI", "db": "Postgres", "cache": "Redis", "queue": "Rabbit"},
            "deployment_strategy": "Docker with Kubernetes and auto-scaling configuration settings.",
            "security_considerations": ["Auth", "TLS", "Rate limit"],
        }
        errors = validate_artifact("architect", data)
        assert any("Too few components" in e for e in errors)

    def test_architecture_too_few_tech_stack(self):
        data = {
            "title": "Arch",
            "overview": "Overview of architecture with enough text to pass minimum length checks.",
            "architecture_pattern": "Layered",
            "components": [
                {"name": "API", "description": "API layer handling all HTTP requests to the system.", "technology": "FastAPI", "responsibilities": ["Route requests", "Auth users"], "dependencies": []},
                {"name": "Service", "description": "Service layer implementing core business logic processing.", "technology": "Python", "responsibilities": ["Business logic", "Data validation"], "dependencies": []},
                {"name": "DB", "description": "Database layer for persistent storage of all application data.", "technology": "PostgreSQL", "responsibilities": ["Store data", "Run queries"], "dependencies": []},
            ],
            "data_flow": [{"step": "1", "description": "Request"}, {"step": "2", "description": "Process"}, {"step": "3", "description": "Query"}, {"step": "4", "description": "Response"}],
            "tech_stack": {"lang": "Python"},
            "deployment_strategy": "Docker Compose for development and Kubernetes for production workloads.",
            "security_considerations": ["Auth", "TLS", "Rate limit"],
        }
        errors = validate_artifact("architect", data)
        assert any("Too few tech stack entries" in e for e in errors)

    def test_developer_no_files(self):
        data = {"root": "project", "files": []}
        errors = validate_artifact("developer", data)
        assert any("No files generated" in e for e in errors)

    def test_developer_no_main_file(self):
        data = {"root": "project", "files": [{"path": "utils.py", "content": "", "language": "python"}]}
        errors = validate_artifact("developer", data)
        assert any("No main entry point" in e for e in errors)

    def test_tester_no_test_cases(self):
        data = {"test_framework": "pytest", "test_config": {}, "test_cases": [], "coverage_target": 0.8}
        errors = validate_artifact("tester", data)
        assert any("No test cases" in e for e in errors)

    def test_code_review_score_out_of_range(self):
        data = {
            "summary": "Good",
            "overall_score": 15.0,
            "comments": [],
            "strengths": [],
            "weaknesses": [],
            "security_concerns": [],
        }
        errors = validate_artifact("code_review", data)
        assert len(errors) > 0

    def test_documentation_missing_readme(self):
        data = {
            "readme": "",
            "setup_guide": "# Setup",
        }
        errors = validate_artifact("documentation", data)
        assert any("README is missing" in e for e in errors)

    def test_documentation_with_readme_passes(self):
        data = {
            "readme": "# Project",
            "setup_guide": "# Setup",
        }
        errors = validate_artifact("documentation", data)
        assert errors == []
