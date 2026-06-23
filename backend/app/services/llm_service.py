from __future__ import annotations

from typing import Any, Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.core.exceptions import LLMException
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for interacting with OpenAI LLM.

    Provides structured output generation with retry logic,
    token tracking, and error handling.
    """

    def __init__(self) -> None:
        self._client: Optional[AsyncOpenAI] = None

    async def initialize(self) -> None:
        """Initialize the OpenAI-compatible client."""
        if not settings.OPENAI_API_KEY:
            logger.warning("openai_api_key_not_configured")
            return
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
            logger.info("using_custom_base_url", base_url=settings.OPENAI_BASE_URL)
        self._client = AsyncOpenAI(**client_kwargs)
        logger.info("llm_service_initialized", model=settings.OPENAI_MODEL)

    @property
    def is_available(self) -> bool:
        return self._client is not None

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Optional[type] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> tuple[Any, dict[str, int]]:
        """Generate a response from the LLM.

        Args:
            system_prompt: System-level instruction prompt.
            user_prompt: User message / task description.
            response_model: Optional Pydantic model for structured output.
            temperature: Override default temperature.
            max_tokens: Override default max tokens.

        Returns:
            Tuple of (parsed_response, token_usage_dict).

        Raises:
            LLMException: If the LLM call fails after retries.
        """
        if not self._client:
            raise LLMException("OpenAI client not initialized")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature or settings.OPENAI_TEMPERATURE,
            "max_tokens": max_tokens or settings.OPENAI_MAX_TOKENS,
        }

        if response_model is not None:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self._call_with_retry(**kwargs)
        except Exception as e:
            raise LLMException(f"LLM call failed after retries: {e}") from e

        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
            "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }

        content = response.choices[0].message.content or ""

        if response_model is not None:
            import json

            try:
                parsed = response_model.model_validate_json(content)
            except Exception as e:
                raise LLMException(
                    f"Failed to parse LLM response into {response_model.__name__}: {e}",
                    details={"raw_content": content[:500]},
                )
        else:
            parsed = content

        logger.info(
            "llm_generation_completed",
            model=settings.OPENAI_MODEL,
            token_usage=token_usage,
        )

        return parsed, token_usage

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    async def _call_with_retry(self, **kwargs: Any) -> Any:
        """Make the actual OpenAI API call with retry logic."""
        return await self._client.chat.completions.create(**kwargs)  # type: ignore[union-attr]

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        if not self._client:
            raise LLMException("OpenAI client not initialized")

        try:
            response = await self._client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            raise LLMException(f"Embedding generation failed: {e}") from e


llm_service = LLMService()
