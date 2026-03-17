"""Simulate impact API endpoint."""

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.event import SimulateEventInput
from app.models.result import SimulateImpactResult
from app.services.simulation import run_simulation
from app.core.config import get_settings
from app.core.cache import get_cached, set_cached
from app.core.security import verify_api_key

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["simulate"])


def _cache_key(event_type, source_node, severity):
    return f"impact:sim:{event_type}:{source_node}:{severity:.2f}"


@router.post("/simulate-impact", response_model=SimulateImpactResult)
@limiter.limit("30/minute")
async def simulate_impact(request: Request, event: SimulateEventInput):
    """Run impact simulation for an event."""
    settings = get_settings()
    cache_key = _cache_key(event.event_type, event.source_node, event.severity)
    cached = await get_cached(cache_key)
    if cached:
        return SimulateImpactResult(**cached)

    event_dict = event.model_dump(mode="json")
    result = await run_simulation(event_dict)

    await set_cached(cache_key, result, settings.simulation_cache_ttl)
    return SimulateImpactResult(**result)
