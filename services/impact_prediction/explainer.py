"""Explainability - narrative and reasoning path generation."""

from typing import List


def build_reasoning_path(event: dict, propagation_path: List[str], impact_type: str, entities: List[dict]) -> List[dict]:
    """Build machine-readable reasoning path."""
    path = [{"node": "event", "type": event.get("event_type", "unknown"), "label": (event.get("title") or "")[:80]}]
    for entity_id in propagation_path:
        ent = next((e for e in entities if e.get("entity_id") == entity_id), None)
        label = ent.get("name", entity_id) if ent else entity_id
        path.append({"node": entity_id, "type": "entity", "label": label})
    path.append({"node": "impact", "type": impact_type, "label": impact_type.replace("_", " ").title()})
    return path


def build_narrative(event: dict, propagation_path: List[str], impact_type: str, entities: List[dict]) -> str:
    """Build human-readable narrative."""
    event_title = (event.get("title") or "Event")[:60]
    parts = [f"{event_title} (severity {event.get('severity', 0)})"]
    for entity_id in propagation_path:
        ent = next((e for e in entities if e.get("entity_id") == entity_id), None)
        name = ent.get("name", entity_id) if ent else entity_id
        parts.append(f"-> {name}")
    impact_label = impact_type.replace("_", " ").title()
    parts.append(f"-> {impact_label}")
    return " ".join(parts)
