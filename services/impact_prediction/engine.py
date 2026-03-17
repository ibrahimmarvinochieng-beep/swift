"""Impact Prediction Engine — main orchestrator."""

from typing import List, Optional

from db.impact_store import get_impact_store
from services.impact_prediction.explainer import build_narrative, build_reasoning_path
from services.impact_prediction.priority_engine import rank_impacts
from services.impact_prediction.scoring import compute_priority_score
from services.impact_prediction.simulation_engine import run_simulation
from utils.logger import logger


def predict_impacts(event: dict) -> List[dict]:
    """Full pipeline: simulate -> explain -> rank -> store. Returns stored impacts."""
    store = get_impact_store()
    event_id = event.get("event_id", "")
    impacts_raw = run_simulation(event)
    if not impacts_raw:
        return []

    ranked = rank_impacts(impacts_raw, top_n=10)
    stored = []
    for imp in ranked:
        impact_id = store.add_impact(
            event_id=event_id,
            impact_type=imp["impact_type"],
            impact_category=imp["impact_category"],
            severity=imp["severity"],
            probability=imp["probability"],
            confidence=imp["confidence"],
            time_horizon=imp["time_horizon"],
            geographic_spread=imp["geographic_spread"],
            affected_region=imp.get("affected_region"),
            simulation_depth=imp["simulation_depth"],
            parent_impact_id=imp.get("parent_impact_id"),
            propagation_path=imp["propagation_path"],
            explanation_id=None,
            priority_score=imp.get("priority_score"),
            tags=[imp["impact_type"], imp["time_horizon"]],
        )
        if impact_id:
            entities = []
            path_ids = imp.get("propagation_path", "").split(" -> ")
            for pid in path_ids:
                ent = store.get_entity(pid)
                if ent:
                    entities.append(ent)
            narrative = build_narrative(event, path_ids, imp["impact_type"], entities)
            reasoning_path = build_reasoning_path(event, path_ids, imp["impact_type"], entities)
            ex_id = store.add_explanation(impact_id, narrative, reasoning_path, [imp.get("rule_id")] if imp.get("rule_id") else None)
            store.update_impact_explanation(impact_id, ex_id)
            stored.append({"impact_id": impact_id, "explanation_id": ex_id, **imp})
    return stored
