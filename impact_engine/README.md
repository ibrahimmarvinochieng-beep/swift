# Swift Impact Simulation Engine

Probabilistic cascading impact engine for global-scale Agentic AI. Simulates how events propagate across the dependency graph.

## Quick Start

```bash
pip install -r requirements.txt
# Ensure Graph Service is running on localhost:8000
uvicorn app.main:app --port 8001
```

## API

**POST /simulate-impact**

```json
{
  "event_id": "evt_123",
  "source_node": "infra:port_mombasa",
  "event_type": "disruption",
  "severity": 0.8,
  "timestamp": "2026-03-17T10:00:00Z"
}
```

## Configuration

| Env Var | Default | Description |
|---------|---------|--------------|
| IMPACT_GRAPH_SERVICE_URL | http://localhost:8000 | Graph Service base URL |
| IMPACT_REDIS_URL | redis://localhost:6379/1 | Redis for caching |
| IMPACT_TIME_DECAY_SCALE_FACTOR | 24 | Time decay scale (hours) |
| IMPACT_AGGREGATION_MODE | max | max or weighted_sum |
| IMPACT_MAX_PROPAGATION_DEPTH | 3 | Graph traversal depth |
| IMPACT_API_KEY | (empty) | API key for auth |

## Tests

```bash
pytest tests/ -v
```
