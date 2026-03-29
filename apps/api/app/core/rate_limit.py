from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, status


class SimpleRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def hit(self, namespace: str, key: str, *, limit: int, window_seconds: int) -> int | None:
        now = monotonic()
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


rate_limiter = SimpleRateLimiter()


def normalize_rate_limit_key(*parts: str | None) -> str:
    values = [part.strip().lower() for part in parts if part and part.strip()]
    return "|".join(values) or "anonymous"


def enforce_http_rate_limit(namespace: str, key: str, *, limit: int, window_seconds: int) -> None:
    retry_after = rate_limiter.hit(namespace, key, limit=limit, window_seconds=window_seconds)
    if retry_after is None:
        return
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please slow down and try again shortly.",
        headers={"Retry-After": str(retry_after)},
    )


def reset_rate_limit(namespace: str, key: str) -> None:
    rate_limiter.reset(namespace, key)


def reset_rate_limits() -> None:
    rate_limiter.clear()
