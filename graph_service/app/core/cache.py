"""Redis caching for graph queries."""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import get_settings


_cache: Optional[redis.Redis] = None


async def get_redis() -> Optional[redis.Redis]:
    """Get Redis connection. Returns None if Redis unavailable."""
    global _cache
    if _cache is None:
        try:
            settings = get_settings()
            _cache = redis.from_url(settings.redis_url, decode_responses=True)
            await _cache.ping()
        except Exception:
            _cache = None
    return _cache


def _cache_key(prefix: str, *parts: str) -> str:
    return f"graph:{prefix}:{':'.join(str(p) for p in parts)}"


async def get_cached(key: str) -> Optional[Any]:
    """Get value from cache. Returns None if miss or Redis down."""
    r = await get_redis()
    if not r:
        return None
    try:
        val = await r.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


async def set_cached(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in cache. Returns True on success."""
    r = await get_redis()
    if not r:
        return False
    try:
        await r.set(key, json.dumps(value), ex=ttl)
        return True
    except Exception:
        return False


async def invalidate_pattern(prefix: str) -> int:
    """Invalidate keys matching prefix. Returns count invalidated."""
    r = await get_redis()
    if not r:
        return 0
    try:
        keys = []
        async for k in r.scan_iter(match=f"graph:{prefix}:*"):
            keys.append(k)
        if keys:
            await r.delete(*keys)
        return len(keys)
    except Exception:
        return 0


async def invalidate_graph_cache_on_write() -> int:
    """Invalidate query caches after node/edge writes (deps, impact, weighted-paths)."""
    total = 0
    for prefix in ("deps", "impact", "weighted"):
        total += await invalidate_pattern(prefix)
    return total
