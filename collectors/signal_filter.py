"""Signal filtering — removes noise before AI processing.

Filters applied:
  1. Minimum text length
  2. Keyword relevance scoring
  3. Trusted source whitelist bonus
  4. Source reliability score (0–1) from source_reliability module
"""

from typing import List, Tuple
from utils.logger import logger
from collectors.source_reliability import get_source_reliability_from_signal

MIN_TEXT_LENGTH = 40

EVENT_KEYWORDS = [
    "earthquake", "flood", "fire", "explosion", "attack", "crash", "storm",
    "hurricane", "tornado", "tsunami", "outbreak", "pandemic", "emergency",
    "evacuation", "collapse", "power outage", "disruption", "protest",
    "riot", "conflict", "shooting", "bomb", "derailment", "landslide",
    "volcano", "drought", "famine", "sanctions", "coup", "assassination",
    "hostage", "embargo", "blackout", "cyberattack", "breach", "leak",
    "recall", "contamination", "alert", "warning", "declared", "breaking",
]

TRUSTED_SOURCES = {
    "reuters", "bbc", "ap news", "al jazeera", "associated press",
    "gdacs", "openweathermap", "usgs", "who", "cdc", "un",
    "the guardian", "nyt", "washington post", "afp",
}


def keyword_score(text: str) -> float:
    text_lower = text.lower()
    matches = sum(1 for kw in EVENT_KEYWORDS if kw in text_lower)
    return min(matches / 3.0, 1.0)


def is_trusted_source(source_name: str) -> bool:
    if not source_name:
        return False
    return source_name.lower().strip() in TRUSTED_SOURCES


def filter_signal(signal: dict) -> Tuple[bool, float]:
    """Returns (passes_filter, relevance_score)."""
    content = signal.get("content", "")

    if len(content) < MIN_TEXT_LENGTH:
        return False, 0.0

    score = keyword_score(content)

    if is_trusted_source(signal.get("source_name", "")):
        score = min(score + 0.3, 1.0)

    reliability = get_source_reliability_from_signal(signal)
    signal["source_reliability_score"] = round(reliability, 3)
    score = min(score + reliability * 0.2, 1.0)

    passes = score >= 0.2
    return passes, score


def filter_signals(signals: List[dict]) -> List[dict]:
    filtered = []
    for signal in signals:
        passes, score = filter_signal(signal)
        if passes:
            signal["relevance_score"] = round(score, 3)
            filtered.append(signal)

    logger.info(
        "signals_filtered",
        total=len(signals),
        passed=len(filtered),
        rejected=len(signals) - len(filtered),
    )
    return filtered
