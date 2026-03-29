from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
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
    jwt_issuer: str = "aegiscore-api"
    jwt_audience: str = "aegiscore-platform"
    access_token_expire_minutes: int = 30
    auth_cookie_name: str = "auth_token"
    auth_role_cookie_name: str = "auth_role"
    auth_cookie_secure: bool = False
    auth_cookie_domain: str | None = None
    auth_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    max_upload_size_bytes: int = 5 * 1024 * 1024
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 60
    write_rate_limit_attempts: int = 12
    write_rate_limit_window_seconds: int = 60
    websocket_rate_limit_attempts: int = 30
    websocket_rate_limit_window_seconds: int = 60
    model_version: str = "2026.03"
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080"
    )

    @field_validator("api_prefix", mode="before")
    @classmethod
    def normalize_api_prefix(cls, value: str | None) -> str:
        return value or "/api/v1"

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_app_env(cls, value: str | None) -> str:
        return (value or "development").strip().lower()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: str | None) -> str:
        if not value:
            return ""
        origins = []
        for origin in str(value).split(","):
            candidate = origin.strip().rstrip("/")
            if not candidate:
                continue
            if candidate == "*":
                raise ValueError("Wildcard CORS origins are not allowed when credentials are enabled")
            if not candidate.startswith(("http://", "https://")):
                raise ValueError("CORS origins must begin with http:// or https://")
            origins.append(candidate)
        return ",".join(dict.fromkeys(origins))

    @model_validator(mode="after")
    def validate_cookie_settings(self) -> "Settings":
        if self.auth_cookie_samesite == "none" and not self.auth_cookie_secure:
            raise ValueError("AUTH_COOKIE_SECURE must be true when AUTH_COOKIE_SAMESITE is set to none")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
