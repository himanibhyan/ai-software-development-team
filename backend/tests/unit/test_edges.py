from __future__ import annotations

from app.graph.edges import (
    route_after_code_review,
    route_after_requirements,
    route_after_architecture,
    route_after_development,
    route_after_testing,
    route_after_documentation,
    route_after_validation,
)
from app.graph.state import create_initial_state


class TestRouteAfterValidation:
    def test_routes_to_requirements_on_success(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["status"] = "running"
        assert route_after_validation(state) == "requirements_agent"

    def test_routes_to_error_handler_on_failure(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["status"] = "failed"
        assert route_after_validation(state) == "error_handler"


class TestRouteAfterRequirements:
    def test_routes_to_architect_when_requirements_exist(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["requirements"] = {"title": "Test"}
        assert route_after_requirements(state) == "architect_agent"

    def test_routes_to_error_when_requirements_missing(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        assert route_after_requirements(state) == "error_handler"


class TestRouteAfterArchitecture:
    def test_routes_to_developer_when_architecture_exists(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["architecture"] = {"components": []}
        assert route_after_architecture(state) == "developer_agent"

    def test_routes_to_error_when_architecture_missing(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        assert route_after_architecture(state) == "error_handler"


class TestRouteAfterDevelopment:
    def test_routes_to_code_review_when_code_exists(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["source_code"] = {"files": []}
        assert route_after_development(state) == "code_review_agent"

    def test_routes_to_error_when_code_missing(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        assert route_after_development(state) == "error_handler"


class TestRouteAfterCodeReview:
    def test_routes_to_tester_when_score_is_good(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["source_code"] = {"files": []}
        state["review_report"] = {"overall_score": 8.5}
        assert route_after_code_review(state) == "tester_agent"

    def test_routes_to_developer_when_score_is_low_and_attempts_remain(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["source_code"] = {"files": []}
        state["review_report"] = {"overall_score": 4.0}
        state["review_attempts"] = 1
        assert route_after_code_review(state) == "developer_agent"

    def test_routes_to_tester_when_max_attempts_reached(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["source_code"] = {"files": []}
        state["review_report"] = {"overall_score": 3.0}
        state["review_attempts"] = 3
        assert route_after_code_review(state) == "tester_agent"

    def test_routes_to_tester_when_no_review_report(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["source_code"] = {"files": []}
        assert route_after_code_review(state) == "tester_agent"

    def test_routes_to_error_when_no_source_code(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        assert route_after_code_review(state) == "error_handler"

    def test_routes_to_tester_when_score_exactly_at_threshold(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["source_code"] = {"files": []}
        state["review_report"] = {"overall_score": 6.0}
        assert route_after_code_review(state) == "tester_agent"


class TestRouteAfterTesting:
    def test_routes_to_documentation_when_tests_exist(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["test_suite"] = {"test_cases": []}
        assert route_after_testing(state) == "documentation_agent"

    def test_routes_to_error_when_tests_missing(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        assert route_after_testing(state) == "error_handler"


class TestRouteAfterDocumentation:
    def test_routes_to_persistence_always(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        state["documentation"] = {"readme": "# Project"}
        assert route_after_documentation(state) == "persistence_node"

    def test_routes_to_persistence_even_without_docs(self, sample_idea: str):
        state = create_initial_state(idea=sample_idea)
        assert route_after_documentation(state) == "persistence_node"
