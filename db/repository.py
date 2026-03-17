"""EventRepository — single source of truth for events and pipeline stats.

Supports two persistence backends controlled by PERSISTENCE_BACKEND env var:
  - "memory"  — pure in-memory (tests, ephemeral workloads)
  - "sqlite"  — write-through to data/swift.db (default for local dev)

The SQLite backend uses a *write-through cache* pattern:
  - Reads come from the in-memory dict (fast, no I/O)
  - Every write is immediately flushed to SQLite (crash-safe)
  - On startup the dict is hydrated from the database

Sensitive fields are encrypted at rest via KeyManager / MultiFernet.
"""

import os
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from utils.security_utils import encrypt_event_fields, decrypt_event_fields, get_key_manager
from utils.logger import logger

_STATS_KEY = "pipeline_stats"


class EventRepository:
    """Thread-safe event store with optional SQLite persistence."""

    def __init__(self, backend: str = "memory", db_path: str = ""):
        self._events: Dict[str, dict] = {}
        self._signals_ingested: int = 0
        self._signals_filtered: int = 0
        self._signals_rejected: int = 0
        self._duplicates_caught: int = 0
        self._pipeline_runs: int = 0
        self._last_pipeline_run: Optional[str] = None
        self._lock = threading.Lock()

        self._store = None
        self._backend_name = backend

        if backend == "sqlite":
            from db.sqlite_store import SQLiteStore
            self._store = SQLiteStore(db_path or None)
            self._hydrate()

    def _hydrate(self):
        """Load existing data from SQLite into memory."""
        if not self._store:
            return
        self._events = self._store.load_all_events()

        stats = self._store.kv_get(_STATS_KEY, {})
        self._signals_ingested = stats.get("signals_ingested", 0)
        self._signals_filtered = stats.get("signals_filtered", 0)
        self._signals_rejected = stats.get("signals_rejected", 0)
        self._duplicates_caught = stats.get("duplicates_caught", 0)
        self._pipeline_runs = stats.get("pipeline_runs", 0)
        self._last_pipeline_run = stats.get("last_pipeline_run")

        logger.info("repository_hydrated", events=len(self._events),
                     pipeline_runs=self._pipeline_runs, backend="sqlite")

    def _persist_stats(self):
        if not self._store:
            return
        self._store.kv_set(_STATS_KEY, {
            "signals_ingested": self._signals_ingested,
            "signals_filtered": self._signals_filtered,
            "signals_rejected": self._signals_rejected,
            "duplicates_caught": self._duplicates_caught,
            "pipeline_runs": self._pipeline_runs,
            "last_pipeline_run": self._last_pipeline_run,
        })

    # ── Events ────────────────────────────────────────────────────────

    def add_event(self, event: dict) -> dict:
        with self._lock:
            eid = event["event_id"]
            event.setdefault("created_at", datetime.now(timezone.utc).isoformat())
            encrypted = encrypt_event_fields(event)
            self._events[eid] = encrypted
            if self._store:
                self._store.put_event(eid, encrypted)
        return event

    def get_event(self, event_id: str) -> Optional[dict]:
        event = self._events.get(event_id)
        if event:
            return decrypt_event_fields(event)
        return None

    def delete_event(self, event_id: str) -> bool:
        with self._lock:
            removed = self._events.pop(event_id, None) is not None
            if removed and self._store:
                self._store.delete_event(event_id)
            return removed

    def list_events(
        self,
        event_type: Optional[str] = None,
        min_severity: Optional[int] = None,
        location: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[dict], int]:
        items = [decrypt_event_fields(e) for e in self._events.values()]

        if event_type:
            items = [e for e in items if e.get("event_type") == event_type]
        if min_severity:
            items = [e for e in items if e.get("severity", 0) >= min_severity]
        if location:
            loc_lower = location.lower()
            items = [e for e in items if loc_lower in (e.get("location") or "").lower()]
        if search:
            q = search.lower()
            items = [
                e for e in items
                if q in (e.get("title") or "").lower()
                or q in (e.get("description") or "").lower()
            ]

        items.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return items[start : start + page_size], total

    def count(self) -> int:
        return len(self._events)

    # ── Key rotation ──────────────────────────────────────────────────

    def re_encrypt_all(self) -> dict:
        """Re-encrypt every stored event with the current (newest) key."""
        km = get_key_manager()
        rotated = 0
        failed = 0
        sensitive_keys = ["description", "raw_text"]

        with self._lock:
            for eid, event in self._events.items():
                if not event.get("_encrypted"):
                    continue
                try:
                    for key in sensitive_keys:
                        if key in event and event[key]:
                            event[key] = km.rotate_token(event[key])
                    rotated += 1
                    if self._store:
                        self._store.put_event(eid, event)
                except Exception as exc:
                    failed += 1
                    logger.error("re_encrypt_failed", event_id=eid, error=str(exc))

        logger.info("re_encrypt_complete", rotated=rotated, failed=failed)
        return {"rotated": rotated, "failed": failed, "total": self.count()}

    # ── Pipeline stats ────────────────────────────────────────────────

    def record_ingestion(self, filtered: int = 0, rejected: int = 0, duplicates: int = 0):
        with self._lock:
            self._signals_ingested += filtered + rejected
            self._signals_filtered += filtered
            self._signals_rejected += rejected
            self._duplicates_caught += duplicates
            self._persist_stats()

    def record_pipeline_run(self):
        with self._lock:
            self._pipeline_runs += 1
            self._last_pipeline_run = datetime.now(timezone.utc).isoformat()
            self._persist_stats()

    def get_stats(self) -> dict:
        return {
            "events_stored": self.count(),
            "signals_ingested": self._signals_ingested,
            "signals_filtered": self._signals_filtered,
            "signals_rejected": self._signals_rejected,
            "duplicates_caught": self._duplicates_caught,
            "pipeline_runs": self._pipeline_runs,
            "last_pipeline_run": self._last_pipeline_run,
        }

    # ── Lifecycle ─────────────────────────────────────────────────────

    @property
    def backend(self) -> str:
        return self._backend_name

    def close(self):
        if self._store:
            self._store.close()


def _create_event_repo() -> EventRepository:
    backend = os.environ.get("PERSISTENCE_BACKEND", "sqlite")
    db_path = os.environ.get("SQLITE_DB_PATH", "")
    return EventRepository(backend=backend, db_path=db_path)


# Singleton — imported by both api/ and pipeline/
event_repo = _create_event_repo()
