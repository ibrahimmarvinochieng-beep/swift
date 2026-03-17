"""Impact propagation model with time decay."""

import math
from typing import Any

from app.core.config import get_settings


def time_decay(latency_hours: float, scale_factor: float | None = None) -> float:
    """time_decay = exp(-latency_hours / scale_factor). Default scale_factor=24."""
    s = get_settings()
    scale = scale_factor or s.time_decay_scale_factor
    return math.exp(-latency_hours / scale) if scale > 0 else 1.0


def propagate_impact(
    base_severity: float,
    edges: list[dict[str, Any]],
    scale_factor: float | None = None,
) -> tuple[float, float]:
    """
    Compute impact along a path.
    Returns (impact_score, total_latency_hours).
    """
    impact = base_severity
    total_latency = 0.0
    for e in edges:
        weight = float(e.get("weight", 0.5))
        confidence = float(e.get("confidence", 0.8))
        latency = float(e.get("latency_hours", 0))
        decay = time_decay(latency, scale_factor)
        impact *= weight * confidence * decay
        total_latency += latency
    return max(0.0, min(1.0, impact)), total_latency


def aggregate_node_impacts(
    impacts: list[dict[str, Any]],
    mode: str | None = None,
) -> tuple[float, float]:
    """
    Aggregate multiple path impacts for the same node.
    mode: "max" or "weighted_sum"
    Returns (aggregated_impact, avg_latency).
    """
    s = get_settings()
    mode = mode or s.aggregation_mode
    if not impacts:
        return 0.0, 0.0
    if mode == "max":
        best = max(impacts, key=lambda x: x["impact"])
        return best["impact"], best["latency"]
    if mode == "weighted_sum":
        total = sum(i["impact"] for i in impacts)
        weights = [i["impact"] for i in impacts]
        wsum = sum(weights)
        if wsum <= 0:
            return 0.0, sum(i["latency"] for i in impacts) / len(impacts)
        avg_lat = sum(i["latency"] * w for i, w in zip(impacts, weights)) / wsum
        return min(1.0, total), avg_lat
    return impacts[0]["impact"], impacts[0]["latency"]
