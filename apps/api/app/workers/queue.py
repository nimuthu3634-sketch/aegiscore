from __future__ import annotations

import redis
from rq import Queue

from app.core.config import get_settings

settings = get_settings()


def get_redis_connection() -> redis.Redis:
    return redis.from_url(settings.redis_url)


def get_queue() -> Queue:
    return Queue("ml", connection=get_redis_connection())
