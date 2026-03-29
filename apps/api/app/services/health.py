from __future__ import annotations

from time import perf_counter

from redis import Redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.schemas.domain import HealthResponse, ServiceStatus


def build_health_response(db: Session) -> HealthResponse:
    settings = get_settings()

    db_started = perf_counter()
    try:
        db.execute(text("SELECT 1"))
        database = ServiceStatus(status="ok", latency_ms=round((perf_counter() - db_started) * 1000, 2))
    except Exception as error:  # pragma: no cover - exercised in runtime only
        database = ServiceStatus(status="error", detail=str(error))

    redis_started = perf_counter()
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        redis_client.ping()
        redis_status = ServiceStatus(status="ok", latency_ms=round((perf_counter() - redis_started) * 1000, 2))
    except Exception as error:  # pragma: no cover - exercised in runtime only
        redis_status = ServiceStatus(status="error", detail=str(error))

    return HealthResponse(app=ServiceStatus(status="ok"), database=database, redis=redis_status)
