"""Unit tests for propagation logic."""

import pytest
from app.services.propagation import time_decay, propagate_impact, aggregate_node_impacts


def test_time_decay_zero_latency():
    assert time_decay(0) == 1.0


def test_time_decay_positive():
    assert 0 < time_decay(24, 24) < 1


def test_propagate_impact_single_edge():
    edges = [{"weight": 0.8, "confidence": 0.9, "latency_hours": 0}]
    impact, lat = propagate_impact(0.5, edges)
    assert impact > 0
    assert lat == 0


def test_propagate_impact_zero_weight():
    edges = [{"weight": 0, "confidence": 0.9, "latency_hours": 0}]
    impact, _ = propagate_impact(0.5, edges)
    assert impact == 0


def test_propagate_impact_missing_data():
    edges = [{}]
    impact, _ = propagate_impact(0.5, edges)
    assert 0 <= impact <= 1


def test_aggregate_max():
    impacts = [{"impact": 0.3, "latency": 10}, {"impact": 0.8, "latency": 5}]
    agg, lat = aggregate_node_impacts(impacts, mode="max")
    assert agg == 0.8
    assert lat == 5


def test_aggregate_empty():
    agg, lat = aggregate_node_impacts([], mode="max")
    assert agg == 0
    assert lat == 0
