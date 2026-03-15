from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    api_v1_prefix: str
    secret_key: str
    access_token_expire_minutes: int
    database_url: str
    redis_url: str
    cors_origins: str

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "AegisCore"),
        app_env=os.getenv("APP_ENV", "development"),
        api_v1_prefix=os.getenv("API_V1_PREFIX", "/api/v1"),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://aegiscore:aegiscore@localhost:5432/aegiscore",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173"),
    )
