"""Event -> Impact Mapper - rule-based hypothesis generation."""

from typing import Dict, List

from db.impact_store import get_impact_store
from utils.logger import logger


def _evaluate_conditions(conditions: dict, event: dict) -> bool:
    """Evaluate rule conditions against event."""
    if not conditions:
        return True
    min_sev = conditions.get("min_severity")
    if min_sev is not None and event.get("severity", 0) < min_sev:
        return False
    return True


def map_event_to_hypotheses(event: dict) -> List[dict]:
    """Map event to impact hypotheses using rules."""
    store = get_impact_store()
    event_type = event.get("event_type", "political_event")
    rules = store.get_rules_for_event_type(event_type)
    hypotheses = []
    for r in rules:
        if not _evaluate_conditions(r["conditions"], event):
            continue
        hypotheses.append({
            "impact_type": r["impact_type"],
            "base_probability": r["base_probability"],
            "base_severity": r["base_severity"],
            "time_horizon": r.get("time_horizon", "immediate"),
            "rule_id": r.get("rule_id"),
        })
    logger.debug("event_mapped_to_hypotheses", event_id=event.get("event_id"), count=len(hypotheses))
    return hypotheses
