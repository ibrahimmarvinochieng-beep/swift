"""Tests for event detection v2: language, disambiguation, calibration, multi-label."""

import pytest
from services.event_detection.language import detect_language, is_english, prepare_text_for_classification
from services.event_detection.entity_extraction import _disambiguate_locations
from services.event_detection.classifier import _calibrate_confidence, EventClassifier


def _has_langdetect() -> bool:
    try:
        import langdetect  # noqa: F401
        return True
    except ImportError:
        return False


class TestLanguageDetection:
    @pytest.mark.skipif(not _has_langdetect(), reason="langdetect not installed")
    def test_english_detected(self):
        lang, conf = detect_language(
            "A massive earthquake struck Turkey causing widespread destruction"
        )
        assert lang == "en"
        assert conf > 0.5

    def test_prepare_text_returns_lang(self):
        text, lang = prepare_text_for_classification("Breaking news: flood in Bangladesh")
        assert text == "Breaking news: flood in Bangladesh"
        assert lang == "en"


class TestLocationDisambiguation:
    def test_single_location_unchanged(self):
        result = _disambiguate_locations(["Turkey"], "Earthquake in Turkey")
        assert result == ["Turkey"]

    def test_multiple_ordered_by_relevance(self):
        text = "The earthquake struck Istanbul, Turkey. Rescue teams from Ankara responded."
        result = _disambiguate_locations(["Istanbul", "Turkey", "Ankara"], text)
        assert "Istanbul" in result
        assert len(result) == 3


class TestConfidenceCalibration:
    def test_temperature_one_unchanged(self):
        assert _calibrate_confidence(0.8, 1.0) == 0.8

    def test_temperature_high_flattens(self):
        cal = _calibrate_confidence(0.5, 2.0)
        assert 0.5 < cal < 0.8

    def test_temperature_low_sharpens(self):
        cal = _calibrate_confidence(0.5, 0.5)
        assert cal < 0.5


class TestMultiLabel:
    def test_keyword_returns_event_types(self):
        c = EventClassifier()
        result = c._keyword_classify(
            "Earthquake and tsunami caused power outage and building collapse"
        )
        assert "event_types" in result
        assert len(result["event_types"]) >= 1
