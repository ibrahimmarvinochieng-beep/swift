"""User profile store — connected apps, preferences, monitored events.

Persists to SQLite (same db as events) for crash-safe storage.
Used by the intelligence layer for personalization and monitoring.
"""

import json
import os
import sqlite3
import threading
from typing import Dict, List, Optional, Set

from utils.logger import logger

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "swift.db")


class UserProfileStore:
    """Thread-safe store for user profiles and monitoring preferences."""

    def __init__(self, db_path: str = _DEFAULT_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_tables()

    def _create_tables(self):
        with self._conn:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    connected_apps TEXT DEFAULT '[]',
                    preferred_topics TEXT DEFAULT '[]',
                    preferred_regions TEXT DEFAULT '[]',
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS user_monitoring (
                    user_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, event_id)
                );

                CREATE TABLE IF NOT EXISTS user_alerts (
                    alert_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    suggested_actions TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    read_at TEXT
                );
            """)
        logger.info("user_profile_store_ready", path=self._path)

    def get_profile(self, user_id: str) -> dict:
        """Get user profile. Returns defaults if not found."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT connected_apps, preferred_topics, preferred_regions FROM user_profiles WHERE user_id = ?",
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            return {
                "user_id": user_id,
                "connected_apps": [],
                "preferred_topics": [],
                "preferred_regions": [],
            }
        return {
            "user_id": user_id,
            "connected_apps": json.loads(row[0] or "[]"),
            "preferred_topics": json.loads(row[1] or "[]"),
            "preferred_regions": json.loads(row[2] or "[]"),
        }

    def update_profile(
        self,
        user_id: str,
        connected_apps: Optional[List[str]] = None,
        preferred_topics: Optional[List[str]] = None,
        preferred_regions: Optional[List[str]] = None,
    ) -> dict:
        """Update user profile. Merges with existing."""
        from datetime import datetime, timezone
        profile = self.get_profile(user_id)
        if connected_apps is not None:
            profile["connected_apps"] = connected_apps
        if preferred_topics is not None:
            profile["preferred_topics"] = preferred_topics
        if preferred_regions is not None:
            profile["preferred_regions"] = preferred_regions

        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                """INSERT OR REPLACE INTO user_profiles
                   (user_id, connected_apps, preferred_topics, preferred_regions, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    user_id,
                    json.dumps(profile["connected_apps"]),
                    json.dumps(profile["preferred_topics"]),
                    json.dumps(profile["preferred_regions"]),
                    now,
                ),
            )
            self._conn.commit()
        return profile

    def get_monitored_event_ids(self, user_id: str) -> Set[str]:
        """Get set of event IDs the user is monitoring."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT event_id FROM user_monitoring WHERE user_id = ?",
                (user_id,),
            )
            return {row[0] for row in cur.fetchall()}

    def add_monitoring(self, user_id: str, event_id: str) -> bool:
        """Add event to user's monitoring list."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT OR IGNORE INTO user_monitoring (user_id, event_id, created_at) VALUES (?, ?, ?)",
                    (user_id, event_id, now),
                )
                self._conn.commit()
                return True
            except Exception:
                return False

    def remove_monitoring(self, user_id: str, event_id: str) -> bool:
        """Remove event from user's monitoring list."""
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM user_monitoring WHERE user_id = ? AND event_id = ?",
                (user_id, event_id),
            )
            self._conn.commit()
            return cur.rowcount > 0

    def add_alert(
        self,
        user_id: str,
        event_id: str,
        alert_type: str,
        title: str,
        body: str,
        suggested_actions: List[str],
    ) -> str:
        """Add an alert for a user. Returns alert_id."""
        import uuid
        from datetime import datetime, timezone
        alert_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                """INSERT INTO user_alerts
                   (alert_id, user_id, event_id, alert_type, title, body, suggested_actions, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (alert_id, user_id, event_id, alert_type, title, body, json.dumps(suggested_actions), now),
            )
            self._conn.commit()
        return alert_id

    def get_alerts(
        self,
        user_id: str,
        limit: int = 20,
        unread_only: bool = False,
    ) -> List[dict]:
        """Get alerts for user, newest first."""
        q = "SELECT alert_id, event_id, alert_type, title, body, suggested_actions, created_at FROM user_alerts WHERE user_id = ?"
        params = [user_id]
        if unread_only:
            q += " AND read_at IS NULL"
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._lock:
            cur = self._conn.execute(q, params)
            rows = cur.fetchall()

        return [
            {
                "alert_id": r[0],
                "event_id": r[1],
                "alert_type": r[2],
                "title": r[3],
                "body": r[4],
                "suggested_actions": json.loads(r[5] or "[]"),
                "created_at": r[6],
            }
            for r in rows
        ]


_user_profile_store: Optional[UserProfileStore] = None


def get_user_profile_store() -> UserProfileStore:
    global _user_profile_store
    if _user_profile_store is None:
        db_path = os.environ.get("SQLITE_DB_PATH", _DEFAULT_PATH)
        _user_profile_store = UserProfileStore(db_path=db_path or _DEFAULT_PATH)
    return _user_profile_store
