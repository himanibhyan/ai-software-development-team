from __future__ import annotations

from app.core.exceptions import (
    AgentException,
    AppException,
    AuthenticationException,
    AuthorizationException,
    LLMException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)


class TestAppException:
    def test_default_message(self):
        exc = AppException()
        assert exc.message == "An application error occurred"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_custom_message_and_status(self):
        exc = AppException("Custom error", status_code=400, details={"key": "val"})
        assert exc.message == "Custom error"
        assert exc.status_code == 400
        assert exc.details == {"key": "val"}

    def test_string_representation(self):
        exc = AppException("test error")
        assert str(exc) == "test error"


class TestNotFoundException:
    def test_default_message(self):
        exc = NotFoundException()
        assert exc.message == "Resource not found"
        assert exc.status_code == 404

    def test_with_entity_and_id(self):
        exc = NotFoundException(entity="User", entity_id="42")
        assert exc.message == "User not found: 42"

    def test_with_details(self):
        exc = NotFoundException(entity="Project", details={"query": "foo"})
        assert exc.message == "Project not found"
        assert exc.details == {"query": "foo"}


class TestValidationException:
    def test_default_message(self):
        exc = ValidationException()
        assert exc.message == "Validation failed"
        assert exc.status_code == 422

    def test_custom_message(self):
        exc = ValidationException("Invalid email format")
        assert exc.message == "Invalid email format"


class TestAuthenticationException:
    def test_default_message(self):
        exc = AuthenticationException()
        assert exc.message == "Authentication failed"
        assert exc.status_code == 401

    def test_with_details(self):
        exc = AuthenticationException(details={"provider": "oauth"})
        assert exc.details == {"provider": "oauth"}


class TestAuthorizationException:
    def test_default_message(self):
        exc = AuthorizationException()
        assert exc.message == "Forbidden"
        assert exc.status_code == 403


class TestAgentException:
    def test_message_includes_agent_type(self):
        exc = AgentException(agent_type="developer", message="Code gen failed")
        assert exc.message == "[developer] Code gen failed"
        assert exc.status_code == 500

    def test_details_includes_agent_type(self):
        exc = AgentException("architect", details={"component": "API"})
        assert exc.details["agent_type"] == "architect"
        assert exc.details["component"] == "API"


class TestLLMException:
    def test_default_message_and_status(self):
        exc = LLMException()
        assert exc.message == "LLM service error"
        assert exc.status_code == 502

    def test_with_details(self):
        exc = LLMException("OpenAI timeout", details={"model": "gpt-4"})
        assert exc.details == {"model": "gpt-4"}


class TestRateLimitException:
    def test_default_message_and_status(self):
        exc = RateLimitException()
        assert exc.message == "Rate limit exceeded"
        assert exc.status_code == 429

    def test_custom_message(self):
        exc = RateLimitException("Too many requests, slow down")
        assert exc.message == "Too many requests, slow down"
