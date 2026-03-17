"""Simulation result output schema."""

from typing import Optional
from pydantic import BaseModel, Field


class AffectedNode(BaseModel):
    node_id: str
    impact: float = Field(..., ge=0, le=1)
    time_to_impact_hours: int | float


class CriticalPath(BaseModel):
    path: list[str]
    cumulative_impact: float
    total_latency_hours: float


class RecommendedAction(BaseModel):
    action: str
    priority: str = "medium"
    target_node: Optional[str] = None


class SimulateImpactResult(BaseModel):
    impact_score: float = Field(..., ge=0, le=1)
    affected_nodes: list[AffectedNode]
    critical_paths: list[CriticalPath]
    time_to_peak_impact: str
    recommended_actions: list[RecommendedAction]
