"""Dependency Graph Service - entity resolution and traversal."""

from typing import Dict, List, Optional

from db.impact_store import get_impact_store
from utils.logger import logger


def resolve_entities_for_location(location: str) -> List[dict]:
    """Resolve graph entities that match event location."""
    store = get_impact_store()
    entities = store.get_entities_in_location(location)
    if not entities and location:
        entity = store.get_entity("geo:" + location.lower().replace(" ", "-")[:50])
        if entity:
            entities = [entity]
    return entities


def get_downstream_entities(entity_id: str) -> List[dict]:
    """Get entities that this entity affects (outgoing edges)."""
    store = get_impact_store()
    edges = store.get_outgoing_edges(entity_id)
    result = []
    for e in edges:
        target = store.get_entity(e["to_entity_id"])
        if target:
            result.append({"entity": target, "edge": e})
    return result


def traverse_for_impact(
    start_entity_ids: List[str],
    max_depth: int = 2,
    cost_limit: int = 100,
) -> List[dict]:
    """BFS traversal from start entities. Returns list of (entity, depth, path)."""
    store = get_impact_store()
    visited = set()
    queue = [(eid, 0, [eid]) for eid in start_entity_ids]
    result = []
    cost = 0
    while queue and cost < cost_limit:
        entity_id, depth, path = queue.pop(0)
        if entity_id in visited:
            continue
        visited.add(entity_id)
        cost += 1
        entity = store.get_entity(entity_id)
        if entity:
            result.append({"entity": entity, "depth": depth, "path": path})
        if depth >= max_depth:
            continue
        for edge in store.get_outgoing_edges(entity_id):
            to_id = edge["to_entity_id"]
            if to_id not in visited:
                queue.append((to_id, depth + 1, path + [to_id]))
    return result
