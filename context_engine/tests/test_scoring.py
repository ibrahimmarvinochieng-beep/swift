"""Unit tests for relevance scoring."""

import pytest
from app.services.scoring import location_match, industry_match, interest_match, behavioral_weight, compute_relevance_score


def test_location_match_no_user_locations():
    assert location_match([], set()) == 0.5


def test_location_match_overlap():
    affected = [{"node_id": "loc:kenya"}, {"node_id": "loc:uganda"}]
    user = {"loc:kenya"}
    assert location_match(affected, user) > 0.5


def test_industry_match():
    affected = [{"node_id": "ind:agriculture"}]
    user = {"ind:agriculture"}
    assert industry_match(affected, user) > 0.5


def test_interest_match():
    event = {"event_type": "disruption", "keywords": ["supply chain"]}
    user_interests = ["supply chain", "logistics"]
    assert interest_match(event, user_interests) > 0.5


def test_behavioral_weight_no_interactions():
    assert behavioral_weight({}, "evt_1") == 0.5


def test_behavioral_weight_with_save():
    counts = {"evt_1:save": 2}
    assert behavioral_weight(counts, "evt_1") > 0.7


def test_compute_relevance_score():
    user = {"locations": ["Kenya"], "industries": ["Agriculture"], "interests": ["logistics"]}
    enriched = {"location_nodes": ["loc:kenya"], "industry_nodes": ["ind:agriculture"]}
    affected = [{"node_id": "loc:kenya"}, {"node_id": "ind:agriculture"}]
    event = {"event_id": "e1", "event_type": "disruption"}
    score = compute_relevance_score(0.8, affected, user, enriched, event, {})
    assert 0 <= score <= 1
