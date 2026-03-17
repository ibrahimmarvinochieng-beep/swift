"""Event-to-user matching engine."""

from typing import Any
import httpx
from app.core.config import get_settings
from app.services.enrichment import enrich_user_context
from app.services.scoring import compute_relevance_score


async def get_impact_for_event(event: dict) -> dict | None:
    """Call Impact Engine to get affected nodes for an event."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                get_settings().impact_engine_url + "/simulate-impact",
                json={
                    "event_id": event.get("event_id", ""),
                    "source_node": event.get("source_node", ""),
                    "event_type": event.get("event_type", "disruption"),
                    "severity": float(event.get("severity", 0.5)),
                },
            )
            if r.status_code == 200:
                return r.json()
    except Exception:
        pass
    return None


async def match_users_to_event(
    event: dict,
    users: list[dict],
    interaction_counts_by_user: dict[str, dict[str, int]],
) -> list[dict[str, Any]]:
    """
    For an event, compute relevance score per user.
    Returns list of {user_id, relevance_score, ...} sorted by score desc.
    """
    impact_data = await get_impact_for_event(event)
    if not impact_data:
        return []

    impact_score = impact_data.get("impact_score", 0)
    affected_nodes = impact_data.get("affected_nodes", [])

    results = []
    for user in users:
        enriched = enrich_user_context(user)
        counts = interaction_counts_by_user.get(user["user_id"], {})
        score = compute_relevance_score(
            impact_score, affected_nodes, user, enriched, event, counts
        )
        results.append({
            "user_id": user["user_id"],
            "relevance_score": round(score, 4),
            "impact_score": impact_score,
        })
    results.sort(key=lambda x: -x["relevance_score"])
    return results
