from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# Map Docker secret filenames (lowercase) to Settings field names
DOCKER_SECRET_MAP: dict[str, str] = {
    "openai_api_key": "OPENAI_API_KEY",
    "secret_key": "SECRET_KEY",
    "api_key": "API_KEY",
    "database_url": "DATABASE_URL",
    "github_token": "GITHUB_TOKEN",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def model_post_init(self, __context: object) -> None:
        """Override secrets from Docker secrets (``/run/secrets/<name>``) if present.

        Docker secrets take precedence over ``.env`` file values.
        This enables production deployments without baking secrets into files.
        """
        self._load_docker_secrets()

    def _load_docker_secrets(self, secrets_dir: Path | None = None) -> None:
        """Load secrets from Docker secrets directory.

        Pass a custom *secrets_dir* in tests to avoid depending on
        ``/run/secrets`` existing.
        """
        secrets_dir = secrets_dir or Path("/run/secrets")
        if not secrets_dir.is_dir():
            return
        for secret_name, field_name in DOCKER_SECRET_MAP.items():
            secret_path = secrets_dir / secret_name
            if secret_path.is_file():
                value = secret_path.read_text().strip()
                object.__setattr__(self, field_name, value)

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
