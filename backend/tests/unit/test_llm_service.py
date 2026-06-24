from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from app.core.exceptions import LLMException
from app.services.llm_service import LLMService


class _DummyResponse(BaseModel):
    result: str
    score: float


class _MockChoice:
    def __init__(self, content: str):
        self.message = MagicMock(content=content)


class _MockUsage:
    def __init__(self, prompt=10, completion=20, total=30):
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = total


class _MockChatResponse:
    def __init__(self, content: str, usage: _MockUsage | None = None):
        self.choices = [_MockChoice(content)]
        self.usage = usage or _MockUsage()


class _MockEmbeddingData:
    def __init__(self, embedding: list[float]):
        self.embedding = embedding


class _MockEmbeddingResponse:
    def __init__(self, embedding: list[float]):
        self.data = [_MockEmbeddingData(embedding)]


@pytest.fixture
def llm() -> LLMService:
    return LLMService()


@pytest.fixture
def mock_openai_client():
    client = AsyncMock()
    client.chat.completions.create = AsyncMock()
    client.embeddings.create = AsyncMock()
    return client


class TestInitialize:
    async def test_initialize_with_api_key(self, llm):
        with (
            patch.object(llm, "_client", None),
            patch("app.services.llm_service.settings.OPENAI_API_KEY", "sk-test"),
            patch("app.services.llm_service.settings.OPENAI_BASE_URL", ""),
            patch("app.services.llm_service.AsyncOpenAI") as mock_client_cls,
        ):
            await llm.initialize()
            mock_client_cls.assert_called_once_with(api_key="sk-test")
            assert llm._client is not None

    async def test_initialize_without_api_key(self, llm):
        with (
            patch.object(llm, "_client", None),
            patch("app.services.llm_service.settings.OPENAI_API_KEY", ""),
            patch("app.services.llm_service.AsyncOpenAI") as mock_client_cls,
        ):
            await llm.initialize()
            mock_client_cls.assert_not_called()
            assert llm._client is None


class TestIsAvailable:
    def test_returns_true_when_client_set(self, llm):
        llm._client = MagicMock()
        assert llm.is_available is True

    def test_returns_false_when_client_none(self, llm):
        llm._client = None
        assert llm.is_available is False


class TestGenerate:
    async def test_raises_when_not_initialized(self, llm):
        llm._client = None
        with pytest.raises(LLMException, match="not initialized"):
            await llm.generate("system", "user")

    async def test_returns_content_and_token_usage(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = _MockChatResponse(
            content="Hello world",
            usage=_MockUsage(prompt=5, completion=15, total=20),
        )

        result, usage = await llm.generate("Be helpful", "Say hello")

        assert result == "Hello world"
        assert usage == {"prompt_tokens": 5, "completion_tokens": 15, "total_tokens": 20}

    async def test_uses_response_model(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = _MockChatResponse(
            content='{"result": "ok", "score": 0.95}',
            usage=_MockUsage(),
        )

        result, usage = await llm.generate("system", "user", response_model=_DummyResponse)

        assert isinstance(result, _DummyResponse)
        assert result.result == "ok"
        assert result.score == 0.95

    async def test_parse_error_raises_llm_exception(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = _MockChatResponse(
            content="not valid json at all",
            usage=_MockUsage(),
        )

        with pytest.raises(LLMException, match="Failed to parse"):
            await llm.generate("system", "user", response_model=_DummyResponse)

    async def test_api_error_raises_llm_exception(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.side_effect = Exception("API timeout")

        with pytest.raises(LLMException, match="LLM call failed after retries"):
            await llm.generate("system", "user")

    async def test_passes_kwargs_to_client(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = _MockChatResponse(
            content="ok",
            usage=None,
        )

        with (
            patch("app.services.llm_service.settings.OPENAI_MODEL", "gpt-4"),
            patch("app.services.llm_service.settings.OPENAI_TEMPERATURE", 0.5),
            patch("app.services.llm_service.settings.OPENAI_MAX_TOKENS", 2048),
        ):
            await llm.generate("sys", "usr", temperature=0.7, max_tokens=1024)

        mock_openai_client.chat.completions.create.assert_called_once()
        _, kwargs = mock_openai_client.chat.completions.create.call_args
        assert kwargs["model"] == "gpt-4"
        assert kwargs["temperature"] == 0.7
        assert kwargs["max_tokens"] == 1024

    async def test_default_temperature_and_max_tokens(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = _MockChatResponse(
            content="ok",
            usage=None,
        )

        with (
            patch("app.services.llm_service.settings.OPENAI_TEMPERATURE", 0.3),
            patch("app.services.llm_service.settings.OPENAI_MAX_TOKENS", 4096),
        ):
            await llm.generate("sys", "usr")

        _, kwargs = mock_openai_client.chat.completions.create.call_args
        assert kwargs["temperature"] == 0.3
        assert kwargs["max_tokens"] == 4096

    async def test_zero_token_usage_when_no_usage(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.chat.completions.create.return_value = _MockChatResponse(
            content="ok",
            usage=_MockUsage(prompt=0, completion=0, total=0),
        )

        _, usage = await llm.generate("sys", "usr")
        assert usage == {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


class TestGenerateEmbedding:
    async def test_returns_embedding(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        expected = [0.1, 0.2, 0.3]
        mock_openai_client.embeddings.create.return_value = _MockEmbeddingResponse(expected)

        result = await llm.generate_embedding("hello")
        assert result == expected

    async def test_raises_when_not_initialized(self, llm):
        llm._client = None
        with pytest.raises(LLMException, match="not initialized"):
            await llm.generate_embedding("text")

    async def test_api_error_raises_llm_exception(self, llm, mock_openai_client):
        llm._client = mock_openai_client
        mock_openai_client.embeddings.create.side_effect = Exception("embedding failed")

        with pytest.raises(LLMException, match="Embedding generation failed"):
            await llm.generate_embedding("text")
