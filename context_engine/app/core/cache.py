"""Redis cache for feeds."""

import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import get_settings

_cache = None


async def get_redis():
    global _cache
    if _cache is None:
        try:
            r = redis.from_url(get_settings().redis_url, decode_responses=True)
            await r.ping()
            _cache = r
        except Exception:
            _cache = None
    return _cache


async def get_cached(key: str) -> Optional[Any]:
    r = await get_redis()
    if not r:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def invalidate_feed(user_id: str) -> int:
    r = await get_redis()
    if not r:
        return 0
    try:
        keys = []
        async for k in r.scan_iter(match=f"feed:{user_id}:*"):
            keys.append(k)
        if keys:
            await r.delete(*keys)
        return len(keys)
    except Exception:
        return 0


async def set_cached(key: str, value: Any, ttl: int = 300) -> bool:
    r = await get_redis()
    if not r:
        return False
    try:
        await r.set(key, json.dumps(value, default=str), ex=ttl)
        return True
    except Exception:
        return False
