"""Source reliability scoring — 0.0 to 1.0 scale.

Uses CRED-1 dataset (2,672 domains) when available for domain-based lookup.
Falls back to manual SOURCE_RELIABILITY for known source names.
CRED-1: https://github.com/aloth/cred-1 (CC BY 4.0)
"""

import json
import os
import re
from typing import Dict, Optional
from urllib.parse import urlparse

from utils.logger import logger

# ── CRED-1 dataset (domain → credibility_score) ─────────────────────
_CRED1: Optional[Dict[str, dict]] = None
_CRED1_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "cred1_current.json"
)


def _load_cred1() -> Dict[str, dict]:
    global _CRED1
    if _CRED1 is not None:
        return _CRED1
    if os.path.exists(_CRED1_PATH):
        try:
            with open(_CRED1_PATH, "r", encoding="utf-8") as f:
                _CRED1 = json.load(f)
            logger.info("cred1_loaded", domains=len(_CRED1), path=_CRED1_PATH)
        except Exception as e:
            logger.warning("cred1_load_failed", path=_CRED1_PATH, error=str(e))
            _CRED1 = {}
    else:
        _CRED1 = {}
        logger.info("cred1_not_found", hint="Run: python scripts/download_cred1.py")
    return _CRED1


def _extract_domain(url: str) -> Optional[str]:
    """Extract hostname from URL, normalized (lowercase, no www)."""
    if not url or not url.strip():
        return None
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or parsed.path).lower()
        if host.startswith("www."):
            host = host[4:]
        return host if host else None
    except Exception:
        return None


# ── Manual fallback for source names (when CRED-1 has no domain) ───
# CRED-1 covers unreliable domains; mainstream news (reuters, bbc) are
# typically NOT in CRED-1, so we use this for known trusted sources.
SOURCE_RELIABILITY: Dict[str, float] = {
    "reuters": 0.95,
    "associated press": 0.95,
    "ap news": 0.95,
    "bbc": 0.92,
    "al jazeera": 0.90,
    "the guardian": 0.88,
    "nyt": 0.88,
    "washington post": 0.88,
    "afp": 0.88,
    "gdacs": 0.92,
    "usgs": 0.95,
    "who": 0.95,
    "cdc": 0.93,
    "un": 0.90,
    "openweathermap": 0.85,
    "reuters world": 0.95,
    "bbc news": 0.92,
    "gdacs alerts": 0.92,
    "rsshub": 0.6,
    "unknown": 0.5,
}

# Source name → domain for CRED-1 lookup
SOURCE_TO_DOMAIN: Dict[str, str] = {
    "reuters": "reuters.com",
    "associated press": "apnews.com",
    "ap news": "apnews.com",
    "bbc": "bbc.com",
    "bbc news": "bbc.com",
    "al jazeera": "aljazeera.com",
    "the guardian": "theguardian.com",
    "nyt": "nytimes.com",
    "washington post": "washingtonpost.com",
    "afp": "afp.com",
    "gdacs": "gdacs.org",
    "gdacs alerts": "gdacs.org",
    "who": "who.int",
    "cdc": "cdc.gov",
    "un": "un.org",
    "openweathermap": "openweathermap.org",
}


def _compute_reliability(source_name: str = "", url: str = "") -> float:
    """Return credibility score 0–1. Uses CRED-1 when domain is in dataset.

    Resolution order:
      1. If url provided: extract domain, look up in CRED-1 → use credibility_score
      2. If source_name maps to domain: look up in CRED-1
      3. Fall back to SOURCE_RELIABILITY[source_name] or 0.75 (unknown = assume trusted)
    """
    cred1 = _load_cred1()

    # 1) Domain from URL
    if url:
        domain = _extract_domain(url)
        if domain and domain in cred1:
            return round(cred1[domain]["credibility_score"], 3)

    # 2) Domain from source name mapping
    if source_name:
        key = source_name.lower().strip()
        domain = SOURCE_TO_DOMAIN.get(key)
        if domain and domain in cred1:
            return round(cred1[domain]["credibility_score"], 3)
        if key in SOURCE_RELIABILITY:
            return SOURCE_RELIABILITY[key]

    # 3) Default: 0.75 for unknown (neutral/trusted until proven otherwise)
    return 0.75


def get_source_reliability(source_name: str = "", url: str = "") -> float:
    """Return credibility score 0–1. Public API."""
    return _compute_reliability(source_name=source_name, url=url)


def get_source_reliability_from_signal(signal: dict) -> float:
    """Convenience: get reliability from a signal dict (source_name + url)."""
    return get_source_reliability(
        source_name=signal.get("source_name", ""),
        url=signal.get("url", ""),
    )


def add_reliability_to_signal(signal: dict) -> dict:
    """Add source_reliability_score to signal. Mutates and returns."""
    signal["source_reliability_score"] = round(
        get_source_reliability_from_signal(signal), 3
    )
    return signal


def is_domain_in_cred1(domain: str) -> bool:
    """Check if domain is in CRED-1 dataset."""
    if not domain:
        return False
    return domain.lower().strip() in _load_cred1()
