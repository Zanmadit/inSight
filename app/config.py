"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from environment / ``.env`` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    OPENAI_API_KEY: str = Field(
        ...,
        description="OpenAI API secret key.",
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4o",
        description="OpenAI model identifier.",
    )
    OPENAI_TEMPERATURE: float = Field(
        default=0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for LLM calls.",
    )

    API_HOST: str = Field(
        default="0.0.0.0",
        description="Host the API server binds to.",
    )
    API_PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port the API server listens on.",
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Python logging level.",
    )
