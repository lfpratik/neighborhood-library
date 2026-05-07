"""Application configuration."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # ------------------------
    # Database
    # ------------------------
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/library",
    )

    # ------------------------
    # Application
    # ------------------------
    environment: str = Field(default="development")  # development | production | test
    debug: bool = Field(default=False)

    # ------------------------
    # Logging
    # ------------------------
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")  # json | console

    # ------------------------
    # API
    # ------------------------
    api_v1_prefix: str = Field(default="/api/v1")

    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://0.0.0.0:3000",
            "http://localhost:8000",
            "http://0.0.0.0:8000",
        ]
    )

    # ------------------------
    # Server
    # ------------------------
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    # ------------------------
    # Pydantic config
    # ------------------------
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
