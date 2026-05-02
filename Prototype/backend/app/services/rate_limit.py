from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import redis

from app.core.config import get_settings


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_seconds: int


_client: Optional[redis.Redis] = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        s = get_settings()
        _client = redis.Redis.from_url(s.redis_url, decode_responses=True)
    return _client


def hit(key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
    """
    Fixed-window rate limit:
      - increments counter for (key, window)
      - sets expiry to window_seconds on first hit
    """
    now = int(time.time())
    window_id = now // window_seconds
    redis_key = f"rl:{key}:{window_id}"

    r = _redis()
    # atomic-ish: INCR then TTL
    count = int(r.incr(redis_key))
    ttl = r.ttl(redis_key)
    if ttl == -1:
        r.expire(redis_key, window_seconds)
        ttl = window_seconds
    remaining = max(0, limit - count)
    allowed = count <= limit
    return RateLimitResult(allowed=allowed, remaining=remaining, reset_seconds=int(ttl if ttl and ttl > 0 else window_seconds))

