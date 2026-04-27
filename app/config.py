"""Application configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # ------------------------
    # Database
    # ------------------------
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/library",
        description="Database connection URL",
    )

    # ------------------------
    # Application
    # ------------------------
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

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
    # Pydantic Settings Config
    # ------------------------
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=False,  # allows DATABASE_URL → database_url
        extra="ignore",  # ignore unused env vars (docker, system, etc.)
    )


settings = Settings()
