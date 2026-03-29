from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AegisCore API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./aegiscore.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    model_version: str = "2026.03"
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8080")

    @field_validator("api_prefix", mode="before")
    @classmethod
    def normalize_api_prefix(cls, value: str | None) -> str:
        return value or "/api/v1"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
