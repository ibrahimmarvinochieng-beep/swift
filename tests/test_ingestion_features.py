"""Tests for ingestion features: retry, timestamps, source reliability, DLQ, rate limiter."""

import os
import tempfile
import pytest
from datetime import datetime, timezone

from utils.time_utils import normalize_timestamp
from collectors.source_reliability import get_source_reliability, add_reliability_to_signal
from ingestion.dlq import push, list_entries, count, remove, clear
from ingestion.source_rate_limiter import SourceRateLimiter


class TestNormalizeTimestamp:
    def test_datetime_utc(self):
        dt = datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc)
        out = normalize_timestamp(dt)
        assert "2026-03-17" in out
        assert "+00:00" in out or "Z" in out

    def test_unix_timestamp(self):
        out = normalize_timestamp(1710680400)  # 2024-03-17
        assert "2024" in out

    def test_none_returns_now(self):
        out = normalize_timestamp(None)
        assert "T" in out and "-" in out

    def test_rfc2822_string(self):
        out = normalize_timestamp("Mon, 01 Jan 2024 12:00:00 GMT")
        assert "2024" in out


class TestSourceReliability:
    def test_known_source(self):
        assert get_source_reliability("Reuters") == 0.95
        assert get_source_reliability("BBC") == 0.92

    def test_unknown_source_default(self):
        assert get_source_reliability("random_blog") == 0.75

    def test_add_reliability_to_signal(self):
        signal = {"source_name": "AP News"}
        add_reliability_to_signal(signal)
        assert signal["source_reliability_score"] == 0.95


class TestDLQ:
    def test_push_and_list(self, tmp_path):
        import ingestion.dlq as dlq
        dlq._dlq_path = None
        os.environ["DLQ_PATH"] = str(tmp_path / "dlq.json")
        clear()
        push({"signal_id": "s1", "content": "test"}, reason="test_reason", error="err")
        assert count() == 1
        entries = list_entries()
        assert len(entries) == 1
        assert entries[0]["reason"] == "test_reason"
        assert entries[0]["signal"]["signal_id"] == "s1"

    def test_remove(self, tmp_path):
        import ingestion.dlq as dlq
        dlq._dlq_path = None
        os.environ["DLQ_PATH"] = str(tmp_path / "dlq2.json")
        clear()
        dlq_id = push({"signal_id": "s2"}, reason="x")
        assert remove(dlq_id) is True
        assert remove(dlq_id) is False
        assert count() == 0


class TestSourceRateLimiter:
    def test_allow_under_limit(self):
        lim = SourceRateLimiter(max_per_minute=5, window_seconds=60.0)
        for _ in range(5):
            assert lim.allow("source_a") is True
        assert lim.allow("source_a") is False

    def test_different_sources_isolated(self):
        lim = SourceRateLimiter(max_per_minute=2, window_seconds=60.0)
        lim.allow("a")
        lim.allow("a")
        assert lim.allow("a") is False
        assert lim.allow("b") is True
