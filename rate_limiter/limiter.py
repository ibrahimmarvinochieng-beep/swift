"""Distributed Token Bucket rate limiter backed by Redis.

The check-and-update logic runs as an atomic Lua script in a single
Redis round-trip — no race conditions, no distributed locks.

Key format:  rl:{user_id}
  - In a Redis Cluster the CRC16 of the full key determines the hash
    slot, giving natural distribution across shards.
  - Keys auto-expire after inactivity (2× fill time, min 60 s) to
    prevent unbounded memory growth at 1 B-user scale.

Falls back to an in-memory token bucket when Redis is unavailable
(local development without Redis).
"""

import math
import os
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

from utils.logger import logger

_LUA_PATH = Path(__file__).parent / "token_bucket.lua"


@dataclass
class RateLimitResult:
    allowed: bool
    remaining_tokens: float
    retry_after: float  # seconds; 0.0 if allowed


# ── In-memory fallback (dev / no Redis) ───────────────────────────

@dataclass
class _MemBucket:
    tokens: float
    last_refreshed: float


class _InMemoryBackend:
    """Thread-safe in-memory token bucket for local development."""

    def __init__(self):
        self._buckets: Dict[str, _MemBucket] = {}
        self._lock = threading.Lock()

    def consume(
        self, key: str, bucket_size: int, refill_rate: float,
        now: float, requested: int,
    ) -> RateLimitResult:
        with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = _MemBucket(tokens=float(bucket_size), last_refreshed=now)
                self._buckets[key] = b

            elapsed = max(0.0, now - b.last_refreshed)
            b.tokens = min(bucket_size, b.tokens + elapsed * refill_rate)
            b.last_refreshed = now

            if b.tokens >= requested:
                b.tokens -= requested
                return RateLimitResult(allowed=True, remaining_tokens=b.tokens, retry_after=0.0)

            retry = (requested - b.tokens) / refill_rate
            return RateLimitResult(allowed=False, remaining_tokens=b.tokens, retry_after=retry)


# ── Redis backend ─────────────────────────────────────────────────

class _RedisBackend:
    def __init__(self, redis_client):
        self._r = redis_client
        self._sha: Optional[str] = None
        self._load_script()

    def _load_script(self):
        lua_src = _LUA_PATH.read_text(encoding="utf-8")
        self._sha = self._r.script_load(lua_src)
        logger.info("lua_script_loaded", sha=self._sha[:12])

    def consume(
        self, key: str, bucket_size: int, refill_rate: float,
        now: float, requested: int,
    ) -> RateLimitResult:
        result = self._r.evalsha(
            self._sha,
            1,           # numkeys
            key,         # KEYS[1]
            str(bucket_size),
            str(refill_rate),
            f"{now:.6f}",
            str(requested),
        )
        allowed = int(result[0]) == 1
        remaining = float(result[1])
        retry = float(result[2])
        return RateLimitResult(allowed=allowed, remaining_tokens=remaining, retry_after=retry)


# ── Public API ────────────────────────────────────────────────────

class TokenBucketLimiter:
    """Distributed token-bucket rate limiter.

    Args:
        bucket_size:  Maximum burst capacity (tokens).
        refill_rate:  Tokens added per second.
        key_prefix:   Redis key prefix (default "rl").
        redis_client: A ``redis.Redis`` instance.  If *None* an
                      in-memory fallback is used (dev mode).
    """

    def __init__(
        self,
        bucket_size: int = 100,
        refill_rate: float = 10.0,
        key_prefix: str = "rl",
        redis_client=None,
    ):
        self.bucket_size = bucket_size
        self.refill_rate = refill_rate
        self.key_prefix = key_prefix

        if redis_client is not None:
            try:
                redis_client.ping()
                self._backend = _RedisBackend(redis_client)
                self._using_redis = True
                logger.info(
                    "rate_limiter_initialized",
                    backend="redis",
                    bucket_size=bucket_size,
                    refill_rate=refill_rate,
                )
            except Exception as exc:
                logger.warning("redis_unavailable_for_rate_limiter", error=str(exc))
                self._backend = _InMemoryBackend()
                self._using_redis = False
        else:
            self._backend = _InMemoryBackend()
            self._using_redis = False
            logger.info("rate_limiter_initialized", backend="in-memory",
                        bucket_size=bucket_size, refill_rate=refill_rate)

    def consume(self, user_id: str, tokens: int = 1) -> RateLimitResult:
        """Try to consume *tokens* from *user_id*'s bucket.

        Returns a ``RateLimitResult`` with ``allowed``, ``remaining_tokens``,
        and ``retry_after`` (seconds until the request could succeed).
        """
        key = f"{self.key_prefix}:{user_id}"
        now = time.time()
        return self._backend.consume(
            key, self.bucket_size, self.refill_rate, now, tokens,
        )

    @property
    def is_distributed(self) -> bool:
        return self._using_redis
