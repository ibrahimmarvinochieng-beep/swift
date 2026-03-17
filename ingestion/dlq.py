"""Dead-letter queue for failed signals.

Stores signals that failed processing (filtering, classification, dedup,
or storage) for later inspection and manual retry.
"""

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from utils.logger import logger

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "dlq.json")
_dlq_lock = threading.Lock()
_dlq: List[dict] = []
_dlq_path: Optional[str] = None


def _get_path() -> str:
    global _dlq_path
    if _dlq_path is None:
        _dlq_path = os.environ.get("DLQ_PATH", _DEFAULT_PATH)
    return _dlq_path


def _load():
    global _dlq
    path = _get_path()
    if not os.path.exists(path):
        _dlq = []
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            _dlq = json.load(f)
    except Exception as e:
        logger.warning("dlq_load_failed", path=path, error=str(e))
        _dlq = []


def _save():
    path = _get_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_dlq, f, indent=2, default=str)
    except Exception as e:
        logger.error("dlq_save_failed", path=path, error=str(e))


def push(signal: dict, reason: str, error: Optional[str] = None) -> str:
    """Append a failed signal to the DLQ. Returns dlq_id."""
    with _dlq_lock:
        if not _dlq:
            _load()
        dlq_id = str(uuid.uuid4())
        entry = {
            "dlq_id": dlq_id,
            "signal": signal,
            "reason": reason,
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }
        _dlq.append(entry)
        _save()
        logger.info("dlq_push", dlq_id=dlq_id, reason=reason, signal_id=signal.get("signal_id"))
        return dlq_id


def list_entries(limit: int = 100, offset: int = 0) -> List[dict]:
    """List DLQ entries (newest first)."""
    with _dlq_lock:
        if not _dlq:
            _load()
        items = list(reversed(_dlq))
        return items[offset : offset + limit]


def count() -> int:
    with _dlq_lock:
        if not _dlq:
            _load()
        return len(_dlq)


def remove(dlq_id: str) -> bool:
    """Remove an entry by dlq_id."""
    with _dlq_lock:
        if not _dlq:
            _load()
        for i, e in enumerate(_dlq):
            if e.get("dlq_id") == dlq_id:
                _dlq.pop(i)
                _save()
                return True
        return False


def clear():
    """Clear all DLQ entries."""
    with _dlq_lock:
        global _dlq
        _dlq = []
        _save()
        logger.info("dlq_cleared")
