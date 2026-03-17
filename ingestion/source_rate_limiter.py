"""Per-source ingestion rate limiter — token bucket per source.

Prevents any single source from flooding the pipeline.
Config: max signals per source per minute.
"""

import time
import threading
from typing import Dict

from utils.config_loader import get_settings
from utils.logger import logger

settings = get_settings()


class SourceRateLimiter:
    """In-memory token bucket per source. Resets every window_seconds."""

    def __init__(
        self,
        max_per_minute: int = 60,
        window_seconds: float = 60.0,
    ):
        self.max_per_minute = max_per_minute
        self.window_seconds = window_seconds
        self._counts: Dict[str, list] = {}  # source -> [timestamp, ...]
        self._lock = threading.Lock()

    def _prune(self, source: str):
        cutoff = time.time() - self.window_seconds
        self._counts[source] = [t for t in self._counts.get(source, []) if t > cutoff]

    def allow(self, source: str) -> bool:
        """Return True if source is under limit."""
        with self._lock:
            self._prune(source)
            timestamps = self._counts.get(source, [])
            if len(timestamps) >= self.max_per_minute:
                return False
            timestamps.append(time.time())
            self._counts[source] = timestamps
            return True

    def remaining(self, source: str) -> int:
        """Return remaining signals allowed for this source in current window."""
        with self._lock:
            self._prune(source)
            return max(0, self.max_per_minute - len(self._counts.get(source, [])))


_source_limiter: SourceRateLimiter = None


def get_source_rate_limiter() -> SourceRateLimiter:
    global _source_limiter
    if _source_limiter is None:
        max_per_min = getattr(settings, "ingestion_max_per_source_per_minute", 60)
        _source_limiter = SourceRateLimiter(max_per_minute=max_per_min)
    return _source_limiter
