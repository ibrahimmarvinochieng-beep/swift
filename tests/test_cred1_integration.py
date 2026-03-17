"""Tests for CRED-1 dataset integration in source reliability."""

import pytest
from collectors.source_reliability import (
    get_source_reliability,
    get_source_reliability_from_signal,
    is_domain_in_cred1,
)


class TestCRED1Integration:
    def test_known_trusted_source_uses_manual_score(self):
        assert get_source_reliability("Reuters") == 0.95
        assert get_source_reliability("BBC") == 0.92

    def test_url_with_cred1_domain_uses_dataset(self):
        # infowars.com is in CRED-1 with low credibility
        score = get_source_reliability(url="https://www.infowars.com/article/123")
        assert 0 < score < 0.5

    def test_signal_with_url_uses_domain_lookup(self):
        signal = {
            "source_name": "Unknown Blog",
            "url": "https://100percentfedup.com/some-article",
        }
        score = get_source_reliability_from_signal(signal)
        assert 0 < score < 0.3

    def test_is_domain_in_cred1(self):
        assert is_domain_in_cred1("infowars.com") is True
        assert is_domain_in_cred1("reuters.com") is False
        assert is_domain_in_cred1("") is False
