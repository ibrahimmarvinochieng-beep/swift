# Impact Prediction Engine — Implementation Plan

**Based on:** IMPACT_PREDICTION_ENGINE_V2_WORLD_CLASS_DESIGN.md  
**Target:** Swift Event Intelligence Platform (main repo)

---

## Phase 1: Foundation (DB + Store)

| Task | Deliverable | Status |
|------|-------------|--------|
| 1.1 | Create `db/impact_store.py` — SQLite tables for impacts, impact_entities, impact_rules, graph_entities, graph_edges, explanations, impact_outcomes | Done |
| 1.2 | Seed default impact rules (event_type → impact_type) | Done |
| 1.3 | Seed minimal graph (entities + edges for demo) | Done |

---

## Phase 2: Event → Impact Mapping

| Task | Deliverable | Status |
|------|-------------|--------|
| 2.1 | `services/impact_prediction/event_mapper.py` — Rule engine, condition evaluation | Done |
| 2.2 | Configurable rules from DB | Done |

---

## Phase 3: Dependency Graph

| Task | Deliverable | Status |
|------|-------------|--------|
| 3.1 | `services/impact_prediction/graph_service.py` — Entity resolution, traversal (BFS) | Done |
| 3.2 | Typed edges with weight, confidence | Done |

---

## Phase 4: Simulation

| Task | Deliverable | Status |
|------|-------------|--------|
| 4.1 | `services/impact_prediction/simulation_engine.py` — Time-aware propagation, cost limits | Done |
| 4.2 | `services/impact_prediction/scoring.py` — Severity, probability, confidence | Done |

---

## Phase 5: Explainability & Priority

| Task | Deliverable | Status |
|------|-------------|--------|
| 5.1 | `services/impact_prediction/explainer.py` — Narrative + reasoning_path | Done |
| 5.2 | `services/impact_prediction/priority_engine.py` — Priority formula, top-N | Done |

---

## Phase 6: API & Pipeline Integration

| Task | Deliverable | Status |
|------|-------------|--------|
| 6.1 | API routes: `GET /api/v1/events/{id}/impacts`, `GET /api/v1/impacts/{id}` | Done |
| 6.2 | Pipeline trigger: run impact prediction after event creation | Done |
| 6.3 | Impact identity hash for deduplication | Done |

---

## Phase 7: Learning Loop (Stub)

| Task | Deliverable | Status |
|------|-------------|--------|
| 7.1 | `impact_outcomes` table + API for feedback ingestion | Pending |

---

## Implementation Order

1. Phase 1 (Foundation)
2. Phase 2 (Mapper)
3. Phase 3 (Graph)
4. Phase 4 (Simulation + Scoring)
5. Phase 5 (Explainability + Priority)
6. Phase 6 (API + Pipeline)
7. Phase 7 (Learning stub)

---

## File Structure

```
swift_project/
├── db/
│   └── impact_store.py          # NEW
├── services/
│   └── impact_prediction/
│       ├── __init__.py
│       ├── event_mapper.py      # NEW
│       ├── graph_service.py     # NEW
│       ├── simulation_engine.py # NEW
│       ├── scoring.py           # NEW
│       ├── explainer.py         # NEW
│       ├── priority_engine.py   # NEW
│       └── engine.py            # NEW (orchestrator)
├── api/
│   └── routes.py                # ADD impact routes
└── pipeline/
    └── processor.py             # ADD impact trigger
```
