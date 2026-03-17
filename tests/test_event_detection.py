"""Tests for event detection pipeline: classifier, entity extraction, structuring."""

import pytest


class TestClassifier:
    def test_keyword_classify_earthquake(self):
        from services.event_detection.classifier import EventClassifier
        c = EventClassifier()
        result = c._keyword_classify(
            "A powerful earthquake of magnitude 7.2 struck southern Turkey early this morning"
        )
        assert result["event_detected"] is True
        assert result["event_type"] == "natural_disaster"
        assert result["confidence"] > 0

    def test_keyword_classify_cyberattack(self):
        from services.event_detection.classifier import EventClassifier
        c = EventClassifier()
        result = c._keyword_classify(
            "Major ransomware cyberattack hits hospital network causing data breach and system outage"
        )
        assert result["event_detected"] is True
        assert result["event_type"] in ["security_incident", "technology_incident"]

    def test_keyword_classify_no_event(self):
        from services.event_detection.classifier import EventClassifier
        c = EventClassifier()
        result = c._keyword_classify(
            "The company announced its quarterly earnings report showing steady growth"
        )
        assert result["confidence"] < 0.5

    def test_empty_text(self):
        from services.event_detection.classifier import EventClassifier
        c = EventClassifier()
        result = c.classify("")
        assert result["event_detected"] is False


class TestStructurer:
    def test_structure_event(self):
        from services.event_detection.structuring import EventStructurer
        s = EventStructurer()
        raw = {
            "event_type": "natural_disaster",
            "title": "Earthquake in Turkey",
            "description": "A powerful earthquake struck killing dozens of people",
            "confidence_score": 0.92,
            "sources": ["reuters"],
            "location": "Turkey",
            "latitude": 37.0,
            "longitude": 35.3,
        }
        result = s.structure(raw)
        assert result["event_type"] == "natural_disaster"
        assert result["severity"] >= 4
        assert result["confidence_score"] == 0.92
        assert "event_id" in result
        assert "created_at" in result

    def test_severity_boost_with_keywords(self):
        from services.event_detection.structuring import EventStructurer
        s = EventStructurer()
        raw = {
            "event_type": "security_incident",
            "description": "Mass casualty event with state of emergency declared after fatal attack destroyed buildings",
            "confidence_score": 0.95,
        }
        result = s.structure(raw)
        assert result["severity"] == 5

    def test_validate_good_event(self):
        from services.event_detection.structuring import EventStructurer
        s = EventStructurer()
        event = {
            "event_id": "abc-123",
            "event_type": "natural_disaster",
            "title": "Test Event",
            "confidence_score": 0.9,
            "severity": 4,
        }
        assert s.validate(event) is True

    def test_validate_missing_field(self):
        from services.event_detection.structuring import EventStructurer
        s = EventStructurer()
        event = {"event_type": "test", "confidence_score": 0.5, "severity": 3}
        assert s.validate(event) is False


class TestEntityExtraction:
    def test_extract_entities(self):
        try:
            from services.event_detection.entity_extraction import EntityExtractor
            e = EntityExtractor()
            entities = e.extract(
                "The earthquake struck Istanbul, Turkey. The Red Cross and United Nations sent aid."
            )
            assert isinstance(entities, dict)
            if "locations" in entities:
                location_texts = [loc.lower() for loc in entities["locations"]]
                assert any("istanbul" in l or "turkey" in l for l in location_texts)
        except (OSError, ModuleNotFoundError):
            pytest.skip("spaCy or model not installed")

    def test_extract_empty_text(self):
        try:
            from services.event_detection.entity_extraction import EntityExtractor
            e = EntityExtractor()
            result = e.extract("")
            assert result == {}
        except (OSError, ModuleNotFoundError):
            pytest.skip("spaCy or model not installed")
