"""Rate limiting backed by Redis using a sliding-window algorithm.

Each bucket is stored as a Redis sorted set keyed by
``{namespace}:{key}``. Members are random UUIDs; scores are Unix timestamps
(float).  A Lua script performs the check-and-record atomically so there are
no race conditions between the ZREMRANGEBYSCORE / ZADD / ZCARD steps.

Falls back transparently to the in-memory deque implementation when Redis is
unavailable (e.g., unit tests that don't start Redis).  The fallback logs a
warning once per process start so it is visible in CI output.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi import HTTPException, status

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Redis sliding-window implementation
# ---------------------------------------------------------------------------

_LUA_SLIDING_WINDOW = """
local key        = KEYS[1]
local now        = tonumber(ARGV[1])
local window     = tonumber(ARGV[2])
local limit      = tonumber(ARGV[3])
local member     = ARGV[4]
local cutoff     = now - window

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)
if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local oldest_ts = tonumber(oldest[2])
    local retry_after = math.max(1, math.ceil(oldest_ts + window - now))
    return {0, retry_after}
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window + 1)
return {1, 0}
"""

_redis_client = None
_redis_script = None
_redis_warned = False


def _get_redis():
    global _redis_client, _redis_script, _redis_warned
    if _redis_client is not None:
        return _redis_client, _redis_script

    try:
        import redis as redis_lib

        from app.core.config import get_settings
        client = redis_lib.from_url(get_settings().redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        script = client.register_script(_LUA_SLIDING_WINDOW)
        _redis_client = client
        _redis_script = script
        return _redis_client, _redis_script
    except Exception as exc:
        if not _redis_warned:
            _log.warning(
                "Redis rate limiter unavailable (%s). Falling back to in-process limiter "
                "(not safe across restarts or multiple workers).",
                exc,
            )
            _redis_warned = True
        return None, None


# ---------------------------------------------------------------------------
# In-memory fallback (single-process only)
# ---------------------------------------------------------------------------

class _InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, namespace: str, key: str, *, limit: int, window_seconds: int) -> int | None:
        now = time.monotonic()
        bucket_key = f"{namespace}:{key}"
        with self._lock:
            bucket = self._buckets[bucket_key]
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                return retry_after
            bucket.append(now)
            return None

    def reset(self, namespace: str, key: str) -> None:
        with self._lock:
            self._buckets.pop(f"{namespace}:{key}", None)

    def clear(self) -> None:
        with self._lock:
            self._buckets.clear()


_fallback = _InMemoryRateLimiter()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def _redis_hit(namespace: str, key: str, *, limit: int, window_seconds: int) -> int | None:
    client, script = _get_redis()
    if client is None or script is None:
        return _fallback.hit(namespace, key, limit=limit, window_seconds=window_seconds)

    bucket_key = f"rl:{namespace}:{key}"
    now = time.time()
    try:
        result = script(keys=[bucket_key], args=[now, window_seconds, limit, str(uuid4())])
        allowed, retry_after = int(result[0]), int(result[1])
        return None if allowed else max(1, retry_after)
    except Exception as exc:
        _log.warning("Redis rate limit script failed (%s); using fallback.", exc)
        return _fallback.hit(namespace, key, limit=limit, window_seconds=window_seconds)


def _redis_reset(namespace: str, key: str) -> None:
    client, _ = _get_redis()
    if client is not None:
        try:
            client.delete(f"rl:{namespace}:{key}")
            return
        except Exception:
            pass
    _fallback.reset(namespace, key)


def normalize_rate_limit_key(*parts: str | None) -> str:
    values = [part.strip().lower() for part in parts if part and part.strip()]
    return "|".join(values) or "anonymous"


def enforce_http_rate_limit(namespace: str, key: str, *, limit: int, window_seconds: int) -> None:
    retry_after = _redis_hit(namespace, key, limit=limit, window_seconds=window_seconds)
    if retry_after is None:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please slow down and try again shortly.",
        headers={"Retry-After": str(retry_after)},
    )


def reset_rate_limit(namespace: str, key: str) -> None:
    _redis_reset(namespace, key)


def reset_rate_limits() -> None:
    """Clear all in-memory buckets (test helper; does not flush Redis)."""
    _fallback.clear()


# ---------------------------------------------------------------------------
# Object-style limiter (used by WebSocket route)
# ---------------------------------------------------------------------------

class _RateLimiter:
    """Thin wrapper that delegates to the Redis or in-memory backend."""

    @staticmethod
    def hit(namespace: str, key: str, *, limit: int, window_seconds: int) -> int | None:
        return _redis_hit(namespace, key, limit=limit, window_seconds=window_seconds)


rate_limiter = _RateLimiter()
