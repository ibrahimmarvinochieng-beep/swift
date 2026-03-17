"""Base class for all data source collectors.

Supports:
  - Exponential backoff retry via safe_collect()
  - UTC timestamp normalization in normalize_signal()
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

from utils.logger import logger
from utils.retry import retry_async
from utils.time_utils import normalize_timestamp
from utils.config_loader import get_settings

settings = get_settings()


class BaseCollector(ABC):
    """Base class for all data source collectors.

    Each collector must implement `collect()` which returns a list of
    normalized signal dictionaries ready for the streaming queue.
    """

    name: str = "base"

    def normalize_signal(
        self,
        content: str,
        source_type: str,
        source_name: str,
        url: str = "",
        metadata: dict = None,
        fetched_at: Optional[str] = None,
        published_at=None,
    ) -> dict:
        """Build a normalized signal with UTC timestamps."""
        meta = metadata or {}
        if published_at is not None:
            meta["published_at_raw"] = str(published_at)
            meta["published_at_utc"] = normalize_timestamp(published_at)

        return {
            "signal_id": str(uuid.uuid4()),
            "source_type": source_type,
            "source_name": source_name,
            "content": content,
            "url": url,
            "metadata": meta,
            "fetched_at": normalize_timestamp(fetched_at) if fetched_at else datetime.now(timezone.utc).isoformat(),
        }

    @abstractmethod
    async def collect(self) -> List[dict]:
        raise NotImplementedError

    async def safe_collect(self) -> List[dict]:
        """Collect with exponential backoff retry. Returns [] on final failure."""
        max_retries = getattr(settings, "collector_max_retries", 3)
        base_delay = getattr(settings, "collector_retry_base_delay", 1.0)
        max_delay = getattr(settings, "collector_retry_max_delay", 60.0)

        try:
            return await retry_async(
                lambda: self.collect(),
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                context=f"collector:{self.name}",
            )
        except Exception as e:
            logger.error("collector_error", collector=self.name, error=str(e))
            return []
