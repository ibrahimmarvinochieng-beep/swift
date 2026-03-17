"""Impact simulation orchestration."""

from typing import Any

from app.core.config import get_settings
from app.services.graph_client import GraphServiceClient, GraphServiceError
from app.services.scoring import simulate, aggregate, detect_critical_paths, detect_bottlenecks
from app.models.result import AffectedNode, CriticalPath, RecommendedAction


def _format_time_to_peak(hours: float) -> str:
    if hours < 1:
        return f"{int(hours * 60)}m"
    if hours < 24:
        return f"{int(hours)}h"
    return f"{int(hours / 24)}d"


def _build_recommended_actions(
    affected_nodes: list[dict],
    critical_paths: list[dict],
    bottlenecks: list[str],
) -> list[RecommendedAction]:
    actions = []
    if affected_nodes:
        top = affected_nodes[0]
        actions.append(
            RecommendedAction(
                action=f"Monitor {top['node_id']} for cascading impact",
                priority="high",
                target_node=top["node_id"],
            )
        )
    for bn in bottlenecks[:3]:
        actions.append(
            RecommendedAction(
                action=f"Assess bottleneck at {bn}",
                priority="medium",
                target_node=bn,
            )
        )
    if not actions:
        actions.append(RecommendedAction(action="No immediate action required", priority="low"))
    return actions


async def run_simulation(event: dict) -> dict[str, Any]:
    """
    Run full impact simulation.
    event: {event_id, source_node, event_type, severity, timestamp}
    """
    settings = get_settings()
    client = GraphServiceClient()
    source_node = event["source_node"]
    severity = float(event["severity"])
    max_depth = settings.max_propagation_depth
    max_paths = settings.max_paths_per_request

    try:
        data = await client.get_propagation_paths(
            source_node,
            max_depth=max_depth,
            min_weight=0.0,
            limit=max_paths,
        )
    except GraphServiceError:
        return _empty_result("Graph service unavailable")

    paths = data.get("paths", [])
    if not paths:
        return _empty_result("No propagation paths found")

    results = simulate(paths, severity)
    affected_list = aggregate(results)
    critical = detect_critical_paths(paths, severity, top_n=5)
    bottlenecks = detect_bottlenecks(affected_list, critical)

    impact_score = affected_list[0]["impact"] if affected_list else 0.0
    peak_latency = max((a["time_to_impact_hours"] for a in affected_list), default=0)
    time_to_peak = _format_time_to_peak(peak_latency)

    return {
        "impact_score": round(impact_score, 4),
        "affected_nodes": [{"node_id": a["node_id"], "impact": a["impact"], "time_to_impact_hours": a["time_to_impact_hours"]} for a in affected_list[:50]],
        "critical_paths": [{"path": c["path"], "cumulative_impact": c["cumulative_impact"], "total_latency_hours": c["total_latency_hours"]} for c in critical],
        "time_to_peak_impact": time_to_peak,
        "recommended_actions": [{"action": ra.action, "priority": ra.priority, "target_node": ra.target_node} for ra in _build_recommended_actions(affected_list, critical, bottlenecks)],
    }


def _empty_result(message: str) -> dict[str, Any]:
    return {
        "impact_score": 0.0,
        "affected_nodes": [],
        "critical_paths": [],
        "time_to_peak_impact": "0h",
        "recommended_actions": [{"action": message, "priority": "low", "target_node": None}],
    }
