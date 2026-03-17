"""Tests for SQLite persistence — prove data survives restart."""

import os
import tempfile
import pytest

from db.sqlite_store import SQLiteStore
from db.repository import EventRepository


class TestSQLiteStore:
    def _make_store(self, tmp_path):
        db_path = os.path.join(tmp_path, "test.db")
        return SQLiteStore(db_path), db_path

    def test_event_roundtrip(self, tmp_path):
        store, _ = self._make_store(tmp_path)
        store.put_event("e1", {"event_id": "e1", "title": "Hello", "created_at": "2026-01-01"})
        events = store.load_all_events()
        assert "e1" in events
        assert events["e1"]["title"] == "Hello"
        store.close()

    def test_event_delete(self, tmp_path):
        store, _ = self._make_store(tmp_path)
        store.put_event("e2", {"event_id": "e2", "title": "X", "created_at": ""})
        assert store.delete_event("e2") is True
        assert store.delete_event("e2") is False
        assert store.event_count() == 0
        store.close()

    def test_user_roundtrip(self, tmp_path):
        store, _ = self._make_store(tmp_path)
        store.put_user("alice", {"username": "alice", "role": "admin"})
        users = store.load_all_users()
        assert "alice" in users
        assert users["alice"]["role"] == "admin"
        store.close()

    def test_kv_roundtrip(self, tmp_path):
        store, _ = self._make_store(tmp_path)
        store.kv_set("counter", 42)
        assert store.kv_get("counter") == 42
        assert store.kv_get("missing", "default") == "default"
        store.close()

    def test_wipe(self, tmp_path):
        store, _ = self._make_store(tmp_path)
        store.put_event("e1", {"event_id": "e1", "title": "X", "created_at": ""})
        store.put_user("bob", {"username": "bob"})
        store.kv_set("k", "v")
        store.wipe()
        assert store.load_all_events() == {}
        assert store.load_all_users() == {}
        assert store.kv_get("k") is None
        store.close()

    def test_data_survives_reopen(self, tmp_path):
        """Simulates a process restart: close and reopen the same DB file."""
        store, db_path = self._make_store(tmp_path)
        store.put_event("persist-1", {"event_id": "persist-1", "title": "Survived", "created_at": "2026-03-17"})
        store.put_user("charlie", {"username": "charlie", "role": "analyst"})
        store.kv_set("runs", 5)
        store.close()

        store2 = SQLiteStore(db_path)
        events = store2.load_all_events()
        assert "persist-1" in events
        assert events["persist-1"]["title"] == "Survived"

        users = store2.load_all_users()
        assert "charlie" in users

        assert store2.kv_get("runs") == 5
        store2.close()


class TestEventRepositorySQLite:
    def test_sqlite_backend_persists_events(self, tmp_path):
        db_path = os.path.join(tmp_path, "repo.db")

        repo1 = EventRepository(backend="sqlite", db_path=db_path)
        repo1.add_event({"event_id": "r1", "event_type": "flood", "title": "Big Flood"})
        repo1.add_event({"event_id": "r2", "event_type": "fire", "title": "Wildfire"})
        repo1.record_ingestion(filtered=5, rejected=2)
        repo1.record_pipeline_run()
        repo1.close()

        repo2 = EventRepository(backend="sqlite", db_path=db_path)
        assert repo2.count() == 2
        evt = repo2.get_event("r1")
        assert evt is not None
        assert evt["title"] == "Big Flood"

        stats = repo2.get_stats()
        assert stats["signals_ingested"] == 7
        assert stats["pipeline_runs"] == 1
        repo2.close()

    def test_sqlite_backend_delete_persists(self, tmp_path):
        db_path = os.path.join(tmp_path, "del.db")

        repo1 = EventRepository(backend="sqlite", db_path=db_path)
        repo1.add_event({"event_id": "d1", "event_type": "test", "title": "Gone"})
        repo1.delete_event("d1")
        repo1.close()

        repo2 = EventRepository(backend="sqlite", db_path=db_path)
        assert repo2.get_event("d1") is None
        assert repo2.count() == 0
        repo2.close()

    def test_memory_backend_no_persistence(self):
        repo = EventRepository(backend="memory")
        repo.add_event({"event_id": "m1", "event_type": "test", "title": "Ephemeral"})
        assert repo.count() == 1
        assert repo.backend == "memory"

    def test_re_encrypt_persists_to_sqlite(self, tmp_path):
        db_path = os.path.join(tmp_path, "reenc.db")
        repo = EventRepository(backend="sqlite", db_path=db_path)
        repo.add_event({"event_id": "enc1", "event_type": "test",
                        "title": "T", "description": "secret"})
        result = repo.re_encrypt_all()
        assert result["failed"] == 0
        repo.close()

        repo2 = EventRepository(backend="sqlite", db_path=db_path)
        evt = repo2.get_event("enc1")
        assert evt["description"] == "secret"
        repo2.close()
