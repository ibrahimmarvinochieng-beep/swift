"""SQLite persistence layer — zero-config, crash-safe local storage.

Stores events, users, and pipeline stats as JSON blobs in a single
``data/swift.db`` file with WAL journaling for concurrent access.

Design: *write-through cache*.  The in-memory dicts in EventRepository
and auth._users_store remain the primary read path (fast).  Every
mutation is immediately flushed to SQLite so data survives restarts.
On startup the stores hydrate themselves from the database.
"""

import json
import os
import sqlite3
import threading
from typing import Dict, List, Optional

from utils.logger import logger

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "swift.db")


class SQLiteStore:
    """Unified persistence for events, users, and pipeline counters."""

    def __init__(self, db_path: str = _DEFAULT_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._create_tables()
        logger.info("sqlite_store_opened", path=db_path)

    def _create_tables(self):
        with self._conn:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id   TEXT PRIMARY KEY,
                    data       TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    data     TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS kv (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)

    # ── Events ────────────────────────────────────────────────────

    def put_event(self, event_id: str, data: dict) -> None:
        blob = json.dumps(data, default=str)
        created = data.get("created_at", "")
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO events (event_id, data, created_at) VALUES (?, ?, ?)",
                (event_id, blob, created),
            )
            self._conn.commit()

    def delete_event(self, event_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM events WHERE event_id = ?", (event_id,))
            self._conn.commit()
            return cur.rowcount > 0

    def load_all_events(self) -> Dict[str, dict]:
        cur = self._conn.execute("SELECT event_id, data FROM events")
        events: Dict[str, dict] = {}
        for row in cur.fetchall():
            events[row[0]] = json.loads(row[1])
        return events

    def event_count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM events")
        return cur.fetchone()[0]

    # ── Users ─────────────────────────────────────────────────────

    def put_user(self, username: str, data: dict) -> None:
        blob = json.dumps(data, default=str)
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO users (username, data) VALUES (?, ?)",
                (username, blob),
            )
            self._conn.commit()

    def delete_user(self, username: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM users WHERE username = ?", (username,))
            self._conn.commit()
            return cur.rowcount > 0

    def load_all_users(self) -> Dict[str, dict]:
        cur = self._conn.execute("SELECT username, data FROM users")
        users: Dict[str, dict] = {}
        for row in cur.fetchall():
            users[row[0]] = json.loads(row[1])
        return users

    # ── Key-value (pipeline stats, counters) ──────────────────────

    def kv_set(self, key: str, value) -> None:
        blob = json.dumps(value, default=str)
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                (key, blob),
            )
            self._conn.commit()

    def kv_get(self, key: str, default=None):
        cur = self._conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
        row = cur.fetchone()
        if row is None:
            return default
        return json.loads(row[0])

    # ── Lifecycle ─────────────────────────────────────────────────

    def close(self):
        self._conn.close()
        logger.info("sqlite_store_closed", path=self._path)

    def wipe(self):
        """Delete all data (for testing)."""
        with self._lock:
            self._conn.executescript("""
                DELETE FROM events;
                DELETE FROM users;
                DELETE FROM kv;
            """)
