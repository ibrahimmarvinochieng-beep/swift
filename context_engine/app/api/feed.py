"""Personalized feed API."""

from fastapi import APIRouter, Depends, HTTPException, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repository import get_user, get_user_interaction_counts
from app.services.matching import match_users_to_event
from app.core.cache import get_cached, set_cached
from app.core.config import get_settings
from app.core.security import limiter

router = APIRouter(prefix="/feed", tags=["feed"])


async def _get_events_for_feed():
    """Placeholder - integrate with event store/Kafka."""
    return []


@router.get("/{user_id}")
@limiter.limit("60/minute")
async def get_feed(
    request: Request,
    user_id: str = Path(..., min_length=1, max_length=128),
    limit: int = 20,
    session: AsyncSession = Depends(get_db),
):
    """Get personalized feed for user."""
    cache_key = f"feed:{user_id}:{limit}"
    cached = await get_cached(cache_key)
    if cached:
        return cached

    user = await get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = {"user_id": user.user_id, "locations": user.locations or [], "interests": user.interests or [], "industries": user.industries or []}
    counts = await get_user_interaction_counts(session, user_id)

    events = await _get_events_for_feed()
    if not events:
        out = {"user_id": user_id, "events": [], "total": 0}
        await set_cached(cache_key, out, get_settings().feed_cache_ttl)
        return out

    ranked = []
    for ev in events[:limit * 2]:
        m = await match_users_to_event(ev, [user_dict], {user_id: counts})
        if m:
            ranked.append({"event": ev, "relevance_score": m[0]["relevance_score"]})
    ranked.sort(key=lambda x: -x["relevance_score"])

    out = {"user_id": user_id, "events": ranked[:limit], "total": len(ranked)}
    await set_cached(cache_key, out, get_settings().feed_cache_ttl)
    return out
