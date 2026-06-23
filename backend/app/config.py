from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AI Software Development Team"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = '["http://localhost:3000"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_dev_team"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    DISABLE_CELERY: bool = False

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000
    CHROMA_COLLECTION_PROJECTS: str = "project_artifacts"
    CHROMA_COLLECTION_TEMPLATES: str = "code_templates"
    CHROMA_COLLECTION_MEMORY: str = "agent_memory"

    @property
    def chroma_url(self) -> str:
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"

    # OpenAI / LLM Provider
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.2

    # Security
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    API_KEY: str = ""

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # File Storage
    OUTPUT_DIR: Path = Path("./generated_projects")

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_OWNER: Optional[str] = None


settings = Settings()
