"""Priority & Ranking Engine — rank impacts, select top N."""

from typing import List

from services.impact_prediction.scoring import compute_priority_score


def rank_impacts(impacts: List[dict], top_n: int = 10) -> List[dict]:
    """Rank impacts by priority score, return top N."""
    for imp in impacts:
        if "priority_score" not in imp or imp["priority_score"] is None:
            imp["priority_score"] = compute_priority_score(
                severity=imp.get("severity", 2),
                probability=imp.get("probability", 0.5),
                confidence=imp.get("confidence", 0.5),
                affected_population=imp.get("affected_population"),
                economic_weight=imp.get("economic_weight"),
            )
    sorted_impacts = sorted(impacts, key=lambda x: (x.get("priority_score", 0), x.get("severity", 0)), reverse=True)
    return sorted_impacts[:top_n]
