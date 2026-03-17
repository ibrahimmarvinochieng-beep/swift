"""Relevance scoring engine - modular and configurable."""

from typing import Any
from app.core.config import get_settings


def location_match(affected_nodes: list[dict], user_location_nodes: set[str]) -> float:
    """Score 0-1 based on overlap between affected nodes and user locations."""
    if not user_location_nodes:
        return 0.5
    affected_ids = {n.get("node_id", "") for n in affected_nodes}
    overlap = len(affected_ids & user_location_nodes) / len(user_location_nodes)
    return min(1.0, overlap + 0.3)


def industry_match(affected_nodes: list[dict], user_industry_nodes: set[str]) -> float:
    """Score 0-1 based on overlap between affected nodes and user industries."""
    if not user_industry_nodes:
        return 0.5
    affected_ids = {n.get("node_id", "") for n in affected_nodes}
    overlap = len(affected_ids & user_industry_nodes) / len(user_industry_nodes)
    return min(1.0, overlap + 0.3)


def interest_match(event: dict, user_interests: list[str]) -> float:
    """Score 0-1 based on event type/keywords vs user interests."""
    if not user_interests:
        return 0.5
    event_type = (event.get("event_type") or "").lower()
    keywords = event.get("keywords", []) or []
    all_terms = [event_type] + [str(k).lower() for k in keywords]
    matches = sum(1 for i in user_interests if any(i.lower() in t or t in i.lower() for t in all_terms))
    return min(1.0, 0.3 + matches / max(1, len(user_interests)))


def behavioral_weight(interaction_counts: dict[str, int], event_id: str) -> float:
    """Score 0-1 based on past interactions with similar events. Higher = more engaged."""
    save_key = f"{event_id}:save"
    click_key = f"{event_id}:click"
    view_key = f"{event_id}:view"
    saves = interaction_counts.get(save_key, 0)
    clicks = interaction_counts.get(click_key, 0)
    views = interaction_counts.get(view_key, 0)
    if saves > 0:
        return min(1.0, 0.7 + saves * 0.1)
    if clicks > 0:
        return min(1.0, 0.5 + clicks * 0.1)
    if views > 0:
        return min(1.0, 0.4 + views * 0.05)
    return 0.5


def compute_relevance_score(
    impact_score: float,
    affected_nodes: list[dict],
    user: dict,
    enriched: dict,
    event: dict,
    interaction_counts: dict[str, int],
) -> float:
    """
    Relevance = Impact × LocationMatch × IndustryMatch × InterestMatch × BehavioralWeight
    """
    s = get_settings()
    loc_nodes = set(enriched.get("location_nodes", []))
    ind_nodes = set(enriched.get("industry_nodes", []))
    loc = location_match(affected_nodes, loc_nodes)
    ind = industry_match(affected_nodes, ind_nodes)
    interest = interest_match(event, user.get("interests", []) or [])
    behav = behavioral_weight(interaction_counts, event.get("event_id", ""))

    w_loc = s.location_match_weight if loc_nodes else 0
    w_ind = s.industry_match_weight if ind_nodes else 0
    w_int = s.interest_match_weight if user.get("interests") else 0
    w_behav = s.behavioral_weight
    score = impact_score * (loc if loc_nodes else 1.0) * (ind if ind_nodes else 1.0) * (interest if user.get("interests") else 1.0) * behav
    return min(1.0, max(0.0, score))
