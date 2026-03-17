"""Unit tests for scoring and simulation."""

import pytest
from app.services.scoring import simulate, aggregate, detect_critical_paths, detect_bottlenecks


def test_simulate_empty_paths():
    assert simulate([], 0.5) == {}


def test_simulate_path_with_edges():
    paths = [
        {
            "node_ids": ["a", "b", "c"],
            "edges": [
                {"weight": 0.8, "confidence": 0.9, "latency_hours": 0},
                {"weight": 0.7, "confidence": 0.9, "latency_hours": 0},
            ],
        }
    ]
    results = simulate(paths, 0.5)
    assert "c" in results
    assert len(results["c"]) == 1
    assert 0 < results["c"][0]["impact"] < 1


def test_simulate_path_no_edges():
    paths = [{"node_ids": ["a"], "edges": []}]
    assert simulate(paths, 0.5) == {}


def test_simulate_multiple_paths_same_node():
    paths = [
        {"node_ids": ["a", "b"], "edges": [{"weight": 0.5, "confidence": 0.8, "latency_hours": 0}]},
        {"node_ids": ["a", "c", "b"], "edges": [
            {"weight": 0.6, "confidence": 0.9, "latency_hours": 0},
            {"weight": 0.6, "confidence": 0.9, "latency_hours": 0},
        ]},
    ]
    results = simulate(paths, 0.5)
    assert "b" in results
    assert len(results["b"]) == 2


def test_aggregate():
    results = {
        "n1": [{"impact": 0.8, "latency": 5}, {"impact": 0.3, "latency": 10}],
        "n2": [{"impact": 0.5, "latency": 12}],
    }
    out = aggregate(results)
    assert len(out) == 2
    assert out[0]["impact"] >= out[1]["impact"]


def test_detect_critical_paths():
    paths = [
        {"node_ids": ["a", "b"], "edges": [{"weight": 0.9, "confidence": 0.9, "latency_hours": 0}], "total_latency": 0},
        {"node_ids": ["a", "c"], "edges": [{"weight": 0.3, "confidence": 0.5, "latency_hours": 0}], "total_latency": 0},
    ]
    critical = detect_critical_paths(paths, 0.5, top_n=2)
    assert len(critical) == 2
    assert critical[0]["cumulative_impact"] >= critical[1]["cumulative_impact"]


def test_detect_bottlenecks():
    affected = [{"node_id": "n1"}, {"node_id": "n2"}]
    critical = [{"path": ["a", "n1", "b"]}, {"path": ["a", "n1", "c"]}]
    bottlenecks = detect_bottlenecks(affected, critical)
    assert "n1" in bottlenecks
    assert "a" in bottlenecks
