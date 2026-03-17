"""Impact scoring and critical path detection."""

from collections import defaultdict
from typing import Any

from app.services.propagation import propagate_impact, aggregate_node_impacts


def simulate(
    paths: list[dict[str, Any]],
    base_severity: float,
) -> dict[str, list[dict[str, Any]]]:
    """
    Run propagation simulation over paths.
    paths: list of {node_ids, edges, total_latency, cum_weight, cum_confidence}
    Returns: {node_id: [{impact, latency}, ...]}
    """
    results: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in paths:
        edges = p.get("edges", [])
        if not edges:
            continue
        impact, total_latency = propagate_impact(base_severity, edges)
        node_id = p.get("node_ids", [])[-1] if p.get("node_ids") else None
        if node_id:
            results[node_id].append({"impact": impact, "latency": total_latency})
    return dict(results)


def aggregate(results: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Aggregate per-node impacts into final affected nodes list."""
    out = []
    for node_id, impacts in results.items():
        agg_impact, agg_latency = aggregate_node_impacts(impacts)
        out.append({
            "node_id": node_id,
            "impact": round(agg_impact, 4),
            "time_to_impact_hours": round(agg_latency, 2),
        })
    return sorted(out, key=lambda x: -x["impact"])


def detect_critical_paths(
    paths: list[dict[str, Any]],
    base_severity: float,
    top_n: int = 5,
) -> list[dict[str, Any]]:
    """Identify top N highest-impact paths."""
    scored = []
    for p in paths:
        edges = p.get("edges", [])
        if not edges:
            continue
        impact, total_latency = propagate_impact(base_severity, edges)
        node_ids = p.get("node_ids", [])
        scored.append({
            "path": node_ids,
            "cumulative_impact": round(impact, 4),
            "total_latency_hours": round(total_latency, 2),
        })
    scored.sort(key=lambda x: -x["cumulative_impact"])
    return scored[:top_n]


def detect_bottlenecks(affected_nodes: list[dict], critical_paths: list[dict]) -> list[str]:
    """Nodes that appear in multiple critical paths (high centrality)."""
    from collections import Counter
    node_counts: Counter[str] = Counter()
    for cp in critical_paths:
        for nid in cp.get("path", []):
            node_counts[nid] += 1
    return [n for n, _ in node_counts.most_common(10)]
