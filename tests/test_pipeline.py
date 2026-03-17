"""Tests for the ingestion pipeline — processor, demo collector, repository."""

import pytest
import asyncio
from db.repository import EventRepository
from collectors.demo_collector import DemoCollector
from collectors.signal_filter import filter_signals
from pipeline.processor import process_signal


def _run(coro):
    """Helper to run async code in tests."""
    return asyncio.new_event_loop().run_until_complete(coro)


class TestEventRepository:
    def test_add_and_get(self):
        repo = EventRepository()
        event = {"event_id": "test-1", "event_type": "natural_disaster", "title": "Test"}
        repo.add_event(event)
        assert repo.get_event("test-1") is not None
        assert repo.count() == 1

    def test_delete(self):
        repo = EventRepository()
        repo.add_event({"event_id": "del-1", "event_type": "test", "title": "T"})
        assert repo.delete_event("del-1") is True
        assert repo.delete_event("del-1") is False

    def test_list_with_filters(self):
        repo = EventRepository()
        repo.add_event({"event_id": "a", "event_type": "flood", "severity": 4, "title": "Flood in Texas", "location": "Texas"})
        repo.add_event({"event_id": "b", "event_type": "fire", "severity": 2, "title": "Small fire", "location": "Ohio"})

        events, total = repo.list_events(min_severity=3)
        assert total == 1

        events, total = repo.list_events(location="texas")
        assert total == 1

        events, total = repo.list_events(search="small")
        assert total == 1

    def test_stats(self):
        repo = EventRepository()
        repo.record_ingestion(filtered=10, rejected=3, duplicates=2)
        repo.record_pipeline_run()
        stats = repo.get_stats()
        assert stats["signals_ingested"] == 13
        assert stats["signals_filtered"] == 10
        assert stats["pipeline_runs"] == 1


class TestDemoCollector:
    def test_collect_returns_signals(self):
        collector = DemoCollector(batch_size=3)
        signals = _run(collector.collect())
        assert len(signals) == 3
        for s in signals:
            assert "signal_id" in s
            assert "content" in s
            assert len(s["content"]) > 40

    def test_signals_pass_filter(self):
        collector = DemoCollector(batch_size=5)
        signals = _run(collector.collect())
        filtered = filter_signals(signals)
        assert len(filtered) >= 3


class TestProcessor:
    def test_process_event_signal(self):
        from pipeline.processor import get_deduplicator
        get_deduplicator().reset()

        signal = {
            "signal_id": "proc-test-unique-99",
            "content": "BREAKING: A powerful earthquake and tsunami struck Istanbul, Turkey causing major destruction, building collapses, and emergency evacuations across the city",
            "source_type": "test",
            "source_name": "reuters",
        }
        result = process_signal(signal)
        assert result is not None
        assert result["event_type"] is not None
        assert result["severity"] >= 1
        assert "event_id" in result

    def test_process_noise_signal(self):
        signal = {
            "signal_id": "noise-1",
            "content": "Check out this amazing new recipe for chocolate cake that everyone will love",
            "source_type": "test",
            "source_name": "blog",
        }
        result = process_signal(signal)
        assert result is None

    def test_process_short_signal(self):
        signal = {"signal_id": "short", "content": "hi"}
        result = process_signal(signal)
        assert result is None
