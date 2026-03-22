import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_env: str
    api_prefix: str
    secret_key: str
    access_token_expire_minutes: int
    database_url: str
    redis_url: str
    cors_origins: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    allow_self_registration: bool

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    postgres_db = os.getenv("POSTGRES_DB", "aegiscore")
    postgres_user = os.getenv("POSTGRES_USER", "aegiscore")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "aegiscore")
    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))

    allow_self_registration = os.getenv("ALLOW_SELF_REGISTRATION", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    return Settings(
        app_name=os.getenv("APP_NAME", "AegisCore"),
        app_env=os.getenv("APP_ENV", "development"),
        api_prefix=os.getenv("API_PREFIX", ""),
        secret_key=os.getenv("SECRET_KEY", "change-me"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        database_url=os.getenv(
            "DATABASE_URL",
            f"postgresql+psycopg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}",
        ),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173"),
        postgres_db=postgres_db,
        postgres_user=postgres_user,
        postgres_password=postgres_password,
        postgres_host=postgres_host,
        postgres_port=postgres_port,
        allow_self_registration=allow_self_registration,
    )
