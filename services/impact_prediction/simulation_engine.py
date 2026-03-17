"""Time-Aware Impact Simulation Engine - propagate impacts through graph."""

from typing import Dict, List, Optional

from db.impact_store import get_impact_store
from services.impact_prediction.event_mapper import map_event_to_hypotheses
from services.impact_prediction.graph_service import resolve_entities_for_location, traverse_for_impact
from services.impact_prediction.scoring import compute_geographic_spread
from utils.logger import logger

DECAY_PER_HOP = 0.8
MAX_DEPTH = 2
COST_LIMIT = 50


def run_simulation(
    event: dict,
    max_depth: int = MAX_DEPTH,
    cost_limit: int = COST_LIMIT,
    decay: float = DECAY_PER_HOP,
) -> List[dict]:
    """Run full simulation: hypotheses -> graph traversal -> impact records."""
    store = get_impact_store()
    event_id = event.get("event_id", "")
    location = event.get("location", "")
    hypotheses = map_event_to_hypotheses(event)
    if not hypotheses:
        return []

    entities = resolve_entities_for_location(location)
    if not entities:
        entities = [{"entity_id": "geo:unknown", "entity_type": "location", "name": location or "Unknown", "population": 0, "economic_weight": 0}]

    start_ids = [e["entity_id"] for e in entities]
    traversal = traverse_for_impact(start_ids, max_depth=max_depth, cost_limit=cost_limit)

    impacts_out = []
    for hyp in hypotheses:
        impact_type = hyp["impact_type"]
        base_p = hyp["base_probability"]
        base_sev = hyp["base_severity"]
        time_horizon = hyp.get("time_horizon", "immediate")

        for item in traversal:
            depth = item["depth"]
            path = item["path"]
            entity = item["entity"]
            p = base_p * (decay ** depth)
            if p < 0.1:
                continue
            propagation_path = " -> ".join(path)
            geo_spread = compute_geographic_spread(location, entity.get("name"))
            impact_record = {
                "event_id": event_id,
                "impact_type": impact_type,
                "impact_category": "primary" if depth == 0 else "secondary",
                "severity": min(base_sev + depth, 5),
                "probability": round(p, 4),
                "confidence": round(0.7 * (decay ** depth), 4),
                "time_horizon": time_horizon,
                "geographic_spread": geo_spread,
                "affected_region": entity.get("name"),
                "simulation_depth": depth,
                "parent_impact_id": None,
                "propagation_path": propagation_path,
                "affected_population": entity.get("population"),
                "economic_weight": entity.get("economic_weight"),
                "rule_id": hyp.get("rule_id"),
            }
            impacts_out.append(impact_record)

    logger.info("simulation_complete", event_id=event_id, impacts=len(impacts_out))
    return impacts_out
