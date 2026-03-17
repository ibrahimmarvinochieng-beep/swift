"""Scoring - severity, probability, confidence, geographic spread."""

import math
from typing import Optional


def compute_geographic_spread(location: Optional[str], affected_region: Optional[str]) -> str:
    """Derive geographic spread from location/region."""
    if not location and not affected_region:
        return "unknown"
    text = (location or "") + " " + (affected_region or "")
    text = text.lower()
    if "global" in text or "world" in text:
        return "global"
    if any(c in text for c in ["continent", "europe", "asia", "america"]):
        return "continental"
    if any(c in text for c in ["country", "nation", "chile", "usa"]):
        return "national"
    if any(c in text for c in ["region", "state", "province"]):
        return "regional"
    return "local"


def compute_priority_score(
    severity: int,
    probability: float,
    confidence: float,
    affected_population: Optional[int] = None,
    economic_weight: Optional[float] = None,
) -> float:
    """Priority = w1*severity + w2*prob + w3*conf + w4*pop_norm + w5*econ_norm."""
    sev_norm = severity / 5.0
    pop_norm = 0.0
    if affected_population and affected_population > 0:
        pop_norm = min(1.0, math.log10(1 + affected_population) / 7.0)
    econ_norm = 0.0
    if economic_weight and economic_weight > 0:
        econ_norm = min(1.0, math.log10(1 + economic_weight) / 12.0)
    return (
        0.25 * sev_norm +
        0.25 * probability +
        0.20 * pop_norm +
        0.15 * econ_norm +
        0.15 * confidence
    )
