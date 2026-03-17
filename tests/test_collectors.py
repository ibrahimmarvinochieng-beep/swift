"""Tests for data collectors and signal filtering."""

import pytest
from collectors.base_collector import BaseCollector
from collectors.signal_filter import filter_signal, filter_signals, keyword_score, is_trusted_source


class TestSignalFilter:
    def test_short_text_rejected(self):
        signal = {"content": "short text", "source_name": "bbc"}
        passes, score = filter_signal(signal)
        assert passes is False

    def test_relevant_signal_passes(self):
        signal = {
            "content": "A massive earthquake struck the central region causing widespread destruction and evacuations",
            "source_name": "reuters",
        }
        passes, score = filter_signal(signal)
        assert passes is True
        assert score > 0.3

    def test_irrelevant_signal_rejected(self):
        signal = {
            "content": "The local bakery introduced a new flavor of croissant that customers are enjoying very much today",
            "source_name": "unknown_blog",
        }
        passes, score = filter_signal(signal)
        assert score < 0.3

    def test_trusted_source_boost(self):
        assert is_trusted_source("Reuters") is True
        assert is_trusted_source("BBC") is True
        assert is_trusted_source("random_blog") is False

    def test_keyword_score(self):
        assert keyword_score("earthquake and flood warning issued") > 0
        assert keyword_score("delicious pasta recipe today") == 0

    def test_filter_signals_batch(self):
        signals = [
            {"content": "too short", "source_name": "x"},
            {
                "content": "Hurricane warning issued for Florida coast emergency evacuation ordered by authorities",
                "source_name": "AP News",
            },
            {
                "content": "My cat did something funny today and I wanted to share this moment with the world online",
                "source_name": "blog",
            },
        ]
        result = filter_signals(signals)
        assert len(result) >= 1
        assert any("hurricane" in s["content"].lower() for s in result)


class TestBaseCollector:
    def test_normalize_signal(self):

        class DummyCollector(BaseCollector):
            name = "dummy"
            async def collect(self):
                return []

        c = DummyCollector()
        signal = c.normalize_signal(
            content="Test content here",
            source_type="test",
            source_name="test_source",
            url="https://example.com",
        )
        assert "signal_id" in signal
        assert signal["source_type"] == "test"
        assert signal["content"] == "Test content here"
        assert "fetched_at" in signal
