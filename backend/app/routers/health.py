from fastapi import APIRouter
from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.schemas.common import HealthResponse

router = APIRouter()


def _database_status() -> str:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return "connected"
    except SQLAlchemyError:
        return "unavailable"


def _redis_status(redis_url: str) -> str:
    client: Redis | None = None

    try:
        client = Redis.from_url(redis_url)
        client.ping()
        return "connected"
    except RedisError:
        return "unavailable"
    finally:
        if client is not None:
            client.close()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    settings = get_settings()
    database_status = _database_status()
    redis_status = _redis_status(settings.redis_url)
    overall_status = (
        "ok" if database_status == "connected" and redis_status == "connected" else "degraded"
    )

    return HealthResponse(
        status=overall_status,
        app_name=settings.app_name,
        environment=settings.app_env,
        version="0.1.0",
        database=database_status,
        redis=redis_status,
    )
