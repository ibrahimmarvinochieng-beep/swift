# Impact Prediction Engine V2 — World-Class Architecture

**Swift Event Intelligence Platform**  
**Version:** 2.0 (World-Class Redesign)  
**Status:** System Design Only — No Implementation**

---

## Executive Summary

This document redesigns the Impact Prediction Engine into a production-grade, AI-native, globally scalable system capable of powering real-time decision intelligence for 1 billion users. The architecture emphasizes **causal reasoning**, **explainability**, **continuous learning**, and **cost-aware computation** while maintaining modularity for future ML integration.

---

# 1. FULL UPDATED ARCHITECTURE DIAGRAM (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           SWIFT EVENT INTELLIGENCE PLATFORM — GLOBAL SCALE                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │  Raw Events     │
                                    │  (Multi-Source) │
                                    └────────┬────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: EVENT DEDUPLICATION & NORMALIZATION                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
│  │ Embedding       │  │ Heuristic       │  │ Source          │  │ Canonical       │                     │
│  │ Similarity      │─▶│ Clustering     │─▶│ Reliability     │─▶│ Event           │                     │
│  │ (Vector)       │  │ (Time+Geo)     │  │ Weighting       │  │ Merge           │                     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └────────┬────────┘                     │
└────────────────────────────────────────────────────────────────────────────│──────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: SECURITY & TRUST                                                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                                          │
│  │ Source Trust    │  │ Authenticity     │  │ Data Poisoning   │                                          │
│  │ Scoring         │─▶│ Validation       │─▶│ Detection       │──▶ REJECT or PASS                        │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: EVENT → IMPACT MAPPING (Rule-Based MVP)                                                         │
│  ┌─────────────────┐  ┌─────────────────┐                                                                 │
│  │ Rule Engine     │─▶│ Impact          │                                                                 │
│  │ (Conditions)    │  │ Hypotheses      │                                                                 │
│  └─────────────────┘  └────────┬────────┘                                                                 │
└────────────────────────────────────────────────────────────────────────────│──────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: CAUSAL INTELLIGENCE ENGINE                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                                          │
│  │ Causal          │  │ Historical      │  │ Causal          │                                          │
│  │ Validation      │─▶│ Outcome Check   │─▶│ Confidence      │──▶ Adjusted P(impact)                    │
│  │ (Rule Weights)  │  │ (Past events)   │  │ Modifier        │                                          │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: ADVANCED DEPENDENCY GRAPH                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Typed Edges: logistically_depends_on | economically_depends_on | physically_connected_to            │ │
│  │  Weighted | Confidence | Temporal (valid_from, valid_to) | Directional                               │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐                                                                 │
│  │ Entity          │  │ Traversal       │                                                                 │
│  │ Resolution      │─▶│ (BFS/DFS)      │──▶ Affected entities + paths                                    │
│  └─────────────────┘  └─────────────────┘                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6: TIME-AWARE IMPACT SIMULATION ENGINE                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
│  │ Multi-Step      │  │ Time Horizon    │  │ Probability     │  │ Cost-Aware      │                     │
│  │ Propagation     │─▶│ Propagation     │─▶│ Decay per Hop   │─▶│ Early Stop     │                     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └────────┬────────┘                     │
└────────────────────────────────────────────────────────────────────────────│──────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 7: EXPLAINABILITY LAYER                                                                            │
│  ┌─────────────────┐  ┌─────────────────┐                                                                 │
│  │ Reasoning       │  │ Human + Machine │                                                                 │
│  │ Graph Build     │─▶│ Readable        │──▶ explanation_id, narrative, reasoning_path                    │
│  └─────────────────┘  └─────────────────┘                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 8: PRIORITY & RANKING ENGINE                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                                          │
│  │ Priority        │  │ Top-N           │  │ Personalization │                                          │
│  │ Score Formula   │─▶│ Selection       │─▶│ Tags/Embeddings │──▶ Final Impact List                     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 9: IMPACT STORE + OUTPUT                                                                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                                          │
│  │ Impact          │  │ Dedup (Hash ID)  │  │ Kafka           │                                          │
│  │ Persistence     │─▶│ Deterministic    │─▶│ impacts.final   │──▶ Personal Context | Agentic Actions    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                              │
                                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 10: LEARNING & FEEDBACK LOOP                                                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                     │
│  │ Outcome         │  │ Prediction vs   │  │ Rule/Graph      │  │ Model           │                     │
│  │ Ingestion       │─▶│ Reality Compare │─▶│ Weight Update   │─▶│ Retrain (ML)    │                     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. DETAILED MODULE BREAKDOWN

## 2.1 Event Deduplication & Normalization Layer

| Aspect | Design |
|--------|--------|
| **Responsibility** | Cluster duplicate events, merge into canonical event, assign aggregated confidence |
| **Input** | Raw events from pipeline (multiple sources, same real-world occurrence) |
| **Output** | Canonical event with `canonical_event_id`, `source_ids[]`, `aggregated_confidence`, `source_weights` |

### Deduplication Strategy

1. **Embedding Similarity**
   - Encode event (title + description) → 384-dim vector (e.g. sentence-transformers)
   - Cluster within time window (e.g. 24h) using cosine similarity > 0.85
   - Same location/region boosts match

2. **Heuristic Clustering**
   - Same event_type + overlapping time (±6h) + same location → candidate cluster
   - Fuzzy match on title (Jaccard, Levenshtein)

3. **Source Reliability Weighting**
   - Each source has `reliability_score` (0–1)
   - `aggregated_confidence = Σ(confidence_i × reliability_i) / Σ(reliability_i)`

### Data Model

```
canonical_events
  - canonical_event_id (UUID)
  - merged_at
  - aggregated_confidence
  - source_event_ids[] (FK to raw events)
  - source_weights JSONB
  - canonical_title, canonical_description, etc.

event_clusters
  - cluster_id
  - canonical_event_id
  - raw_event_ids[]
  - similarity_scores JSONB
```

### Integration

- Sits **before** impact prediction in pipeline
- Output: one canonical event per cluster → fed to Security & Trust layer

---

## 2.2 Security & Trust Layer

| Aspect | Design |
|--------|--------|
| **Responsibility** | Validate event authenticity, score source trust, detect poisoning |
| **Input** | Canonical event |
| **Output** | PASS (proceed) or REJECT (drop, log, alert) |

### Components

- **Source Trust Scoring**: Per-source `trust_score` from historical accuracy
- **Authenticity Validation**: Signature verification, rate limits, anomaly (impossible events)
- **Data Poisoning Detection**: Statistical outliers, sudden rule/graph manipulation

---

## 2.3 Causal Intelligence Engine

| Aspect | Design |
|--------|--------|
| **Responsibility** | Validate that event CAUSES predicted impact (not just correlation) |
| **Input** | Impact hypothesis (event_type → impact_type) |
| **Output** | Causal confidence modifier (0–1), adjusted probability |

### MVP Approach

- **Rule Weighting**: Each rule has `causal_evidence_count` (historical validations)
- **Historical Validation**: `impact_outcomes` table stores (event_id, impact_id, occurred: bool)
- **Causal Confidence** = `validated_count / (validated_count + invalidated_count)`
- **Adjusted P** = `P_raw × causal_confidence`

### Future Approach (Bayesian / Causal ML)

- Causal graph: event nodes → intermediate nodes → impact nodes
- Do-calculus / backdoor adjustment for confounders
- Learned from `impact_outcomes` over time

---

## 2.4 Advanced Dependency Graph

| Aspect | Design |
|--------|--------|
| **Responsibility** | Store typed, weighted, temporal relationships; support traversal |
| **Input** | Entity IDs, relationship types, traversal query |
| **Output** | Affected entities, paths, edge weights |

### Typed Relationships

| Type | Meaning | Example |
|------|---------|---------|
| `logistically_depends_on` | Supply chain, transport | Port → Mining export |
| `economically_depends_on` | Trade, finance | Region → Industry |
| `physically_connected_to` | Infrastructure | Road → Port |
| `geographically_contains` | Location hierarchy | Chile → Santiago |
| `supplies` | Commodity flow | Chile → China (copper) |

### Edge Schema

- `weight` (0–1): strength of dependency
- `confidence` (0–1): confidence in relationship
- `valid_from`, `valid_to`: temporal validity
- Directional: `from_entity_id` → `to_entity_id`

---

## 2.5 Time-Aware Impact Simulation Engine

| Aspect | Design |
|--------|--------|
| **Responsibility** | Propagate impacts through graph with time horizons and probability decay |
| **Input** | Impact hypotheses, graph, cost limits |
| **Output** | Impact tree with time-staged propagation |

### Time Horizons

| Horizon | Range | Use |
|---------|-------|-----|
| Immediate | 0–6h | Direct physical impact |
| Short-term | 6–24h | Logistics, travel |
| Medium-term | 1–7 days | Supply chain, markets |
| Long-term | 7+ days | Economic, policy |

### Controls

- `max_depth`: 3 (configurable)
- `early_stopping`: stop when P < 0.1
- `cost_limit`: max graph nodes visited per event

---

## 2.6 Explainability Layer

| Aspect | Design |
|--------|--------|
| **Responsibility** | Generate human + machine-readable reasoning for every impact |
| **Input** | Impact + propagation path |
| **Output** | `explanation_id`, `narrative`, `reasoning_path` (graph) |

### Schema

```
explanations
  - explanation_id
  - impact_id
  - narrative TEXT  -- "Earthquake in Santiago (severity 5) → Port Valparaiso (logistically_depends_on) → Copper export delay"
  - reasoning_path JSONB  -- [{"node": "event", "type": "earthquake"}, {"node": "port-valparaiso", "edge": "logistically_depends_on"}, ...]
  - rule_ids[]  -- which rules contributed
```

---

## 2.7 Priority & Ranking Engine

| Aspect | Design |
|--------|--------|
| **Responsibility** | Rank impacts, select top N |
| **Input** | All impacts for event |
| **Output** | Top N impacts, sorted by priority score |

### Priority Formula

```
priority_score = w1×severity + w2×probability + w3×affected_population_norm + w4×economic_weight_norm + w5×confidence
```

- `affected_population_norm`: 0–1 from population in affected region
- `economic_weight_norm`: 0–1 from GDP/trade weight of affected entities

---

## 2.8 Learning & Feedback Loop

| Aspect | Design |
|--------|--------|
| **Responsibility** | Ingest outcomes, compare to predictions, update weights |
| **Input** | Outcome reports (news, APIs, sensors) |
| **Output** | Updated rule weights, graph weights, model params |

### Feedback Sources

- News APIs (event resolution)
- Manual feedback (analyst corrections)
- Sensor data (e.g. port activity)

---

# 3. UPDATED DATABASE SCHEMA

## 3.1 Event Deduplication

```sql
CREATE TABLE canonical_events (
    canonical_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    aggregated_confidence DECIMAL(5,4) NOT NULL,
    source_event_ids UUID[] NOT NULL,
    source_weights JSONB NOT NULL,
    canonical_title TEXT NOT NULL,
    canonical_description TEXT,
    event_type VARCHAR(64),
    severity SMALLINT,
    location VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE event_clusters (
    cluster_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_event_id UUID NOT NULL REFERENCES canonical_events(canonical_event_id),
    raw_event_ids UUID[] NOT NULL,
    similarity_scores JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 3.2 Advanced Dependency Graph

```sql
CREATE TABLE graph_entities (
    entity_id VARCHAR(128) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    name VARCHAR(255),
    metadata JSONB,
    location_id VARCHAR(128),
    population BIGINT,
    economic_weight DECIMAL(18,4),
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE graph_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id VARCHAR(128) NOT NULL REFERENCES graph_entities(entity_id),
    to_entity_id VARCHAR(128) NOT NULL REFERENCES graph_entities(entity_id),
    relationship_type VARCHAR(64) NOT NULL,
    weight DECIMAL(5,4) NOT NULL CHECK (weight BETWEEN 0 AND 1),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (from_entity_id, to_entity_id, relationship_type)
);

CREATE INDEX idx_graph_edges_from ON graph_edges(from_entity_id);
CREATE INDEX idx_graph_edges_to ON graph_edges(to_entity_id);
CREATE INDEX idx_graph_edges_type ON graph_edges(relationship_type);
```

## 3.3 Impacts (Enhanced)

```sql
CREATE TABLE impacts (
    impact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    impact_identity_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA256(event_id + path + type)
    event_id UUID NOT NULL,
    canonical_event_id UUID REFERENCES canonical_events(canonical_event_id),
    
    impact_type VARCHAR(64) NOT NULL,
    impact_category VARCHAR(32) NOT NULL,
    
    severity SMALLINT NOT NULL CHECK (severity BETWEEN 1 AND 5),
    probability DECIMAL(5,4) NOT NULL CHECK (probability BETWEEN 0 AND 1),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    causal_confidence DECIMAL(5,4),
    
    time_horizon VARCHAR(32),
    time_horizon_min_hours INTEGER,
    time_horizon_max_hours INTEGER,
    
    geographic_spread VARCHAR(32),
    affected_region VARCHAR(128),
    affected_population BIGINT,
    economic_weight DECIMAL(18,4),
    
    simulation_depth INTEGER DEFAULT 0,
    parent_impact_id UUID REFERENCES impacts(impact_id),
    propagation_path TEXT,
    
    explanation_id UUID,
    priority_score DECIMAL(10,4),
    
    tags TEXT[],
    embedding_id VARCHAR(128),
    
    model_version VARCHAR(32),
    raw_scores JSONB,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_impacts_identity ON impacts(impact_identity_hash);
```

## 3.4 Explainability

```sql
CREATE TABLE explanations (
    explanation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    impact_id UUID NOT NULL REFERENCES impacts(impact_id),
    narrative TEXT NOT NULL,
    reasoning_path JSONB NOT NULL,
    rule_ids UUID[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## 3.5 Learning Loop

```sql
CREATE TABLE impact_outcomes (
    outcome_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    impact_id UUID NOT NULL REFERENCES impacts(impact_id),
    event_id UUID NOT NULL,
    
    occurred BOOLEAN NOT NULL,
    occurred_at TIMESTAMPTZ,
    source VARCHAR(64),
    source_url TEXT,
    confidence DECIMAL(5,4),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE prediction_accuracy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id UUID,
    impact_type VARCHAR(64),
    time_bucket TIMESTAMPTZ,
    
    predictions_total INTEGER NOT NULL,
    predictions_correct INTEGER NOT NULL,
    accuracy DECIMAL(5,4),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE feedback_logs (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    impact_id UUID,
    feedback_type VARCHAR(32),
    feedback_value JSONB,
    source VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 4. END-TO-END DATA FLOW

```
Step 1:  Raw events arrive (multi-source)
         ↓
Step 2:  DEDUPLICATION — Embedding + heuristic clustering → canonical_event
         ↓
Step 3:  SECURITY — Trust check, authenticity, poisoning detection → PASS/REJECT
         ↓
Step 4:  MAPPING — Rule engine → impact hypotheses (type, P, severity)
         ↓
Step 5:  CAUSAL — Historical validation → causal_confidence → adjusted P
         ↓
Step 6:  GRAPH — Resolve event location → entities → traverse dependencies
         ↓
Step 7:  SIMULATION — Propagate with time horizons, decay, cost limits
         ↓
Step 8:  EXPLAINABILITY — Build reasoning path → narrative + reasoning_path
         ↓
Step 9:  PRIORITY — Compute priority_score → rank → top N
         ↓
Step 10: DEDUP — impact_identity_hash → skip if exists
         ↓
Step 11: STORE — Persist impacts, emit to Kafka
         ↓
Step 12: LEARNING — Outcome ingestion (async) → update rule/graph weights
```

---

# 5. SIMULATION ALGORITHM (STEP-BY-STEP)

```
ALGORITHM: TimeAwareImpactSimulation(event, hypotheses, graph, config)

INPUT:
  event, hypotheses[], graph, config{max_depth, cost_limit, decay_per_hop}

OUTPUT:
  impact_tree (list of impacts with time, probability, path)

1.  queue = PriorityQueue()
2.  FOR each h in hypotheses:
3.      enqueue(queue, (h, depth=0, path=[], P=h.probability, time_horizon=immediate))
4.  visited = {}
5.  cost = 0
6.  WHILE queue not empty AND cost < config.cost_limit:
7.      (h, depth, path, P, time_horizon) = dequeue(queue)
8.      IF depth > config.max_depth OR P < 0.1: CONTINUE
9.      impact_id = hash(event.id, path, h.type)
10.     IF impact_id in visited: CONTINUE
11.     visited[impact_id] = true
12.     cost += 1
13.     CREATE impact record (h, P, time_horizon, path)
14.     entities = graph.get_affected_entities(h.entity_id)
15.     FOR each (entity, edge) in entities:
16.         IF edge.valid_from <= now <= edge.valid_to:
17.             P_new = P * config.decay_per_hop * edge.weight
18.             time_new = advance_time_horizon(time_horizon, edge.delay_hours)
19.             path_new = path + [entity]
20.             enqueue(queue, (hypothesis_for(entity), depth+1, path_new, P_new, time_new))
21. RETURN impact_tree
```

---

# 6. SCALABILITY & PERFORMANCE DESIGN

## 6.1 Kafka Architecture

```
Topic: events.raw (partitions = 50)
  → Consumer Group: deduplication
  → Output: canonical_events (topic)

Topic: canonical_events (partitions = 50)
  → Consumer Group: impact-prediction
  → Output: impacts.predicted (topic)

Topic: impacts.predicted (partitions = 20)
  → Consumer Groups: personal-context, agentic-actions, learning-loop
```

## 6.2 Worker Scaling

- Partition count = max parallelism
- Auto-scale workers based on consumer lag
- Each partition = one event at a time (ordering per event)

## 6.3 Caching Strategy

| Cache | Key | TTL | Invalidation |
|-------|-----|-----|--------------|
| Graph entities by location | `graph:loc:{id}` | 1h | On graph update |
| Rule set | `rules:all` | 5m | On rule change |
| Impact by event | `impacts:event:{id}` | 10m | On new impact |
| Causal confidence | `causal:{rule_id}` | 1h | On outcome ingest |

## 6.4 Graph Query Optimization

- **PostgreSQL MVP**: Materialized paths for common traversals; recursive CTE with depth limit
- **Neo4j Future**: Native index on (from, type); LIMIT on traversal
- **Hybrid**: Hot paths in Redis, cold in Neo4j

---

# 7. SECURITY DESIGN

## 7.1 Threat Model

| Threat | Description |
|-------|-------------|
| Fake events | Malicious actor injects false events |
| Data poisoning | Corrupt training/feedback data |
| Graph manipulation | Tamper with dependency relationships |
| Source impersonation | Spoof high-trust source |

## 7.2 Mitigation Strategies

| Mitigation | Implementation |
|------------|----------------|
| Source attestation | API keys, signed payloads, rate limits |
| Trust scoring | Per-source accuracy from outcomes |
| Anomaly detection | Statistical outliers in event volume/type |
| RBAC | Admin for rules/graph; analysts read-only |
| Audit logging | All rule changes, graph updates, predictions |
| Input validation | Schema, size limits, sanitization |

---

# 8. FUTURE ML INTEGRATION PLAN

## 8.1 Rule-Based → ML Transition

1. **Phase 1**: Rule-based only; collect `impact_outcomes` for training data
2. **Phase 2**: Train causal model on outcomes; use as `causal_confidence` modifier
3. **Phase 3**: Replace rule hypotheses with ML-generated hypotheses (same schema)
4. **Phase 4**: End-to-end neural simulation (research)

## 8.2 Model Plug Points

- **Hypothesis Generator**: Swap rule engine for ML model (same output schema)
- **Causal Modifier**: Swap historical lookup for learned causal graph
- **Priority Scorer**: Swap formula for learned ranker
- **Embedding**: Add vector for each impact (personalization matching)

## 8.3 Abstraction

```
interface ImpactHypothesisGenerator:
  generate(event) -> List[Hypothesis]

interface CausalValidator:
  validate(hypothesis, event) -> causal_confidence

interface PriorityScorer:
  score(impact) -> priority_score
```

Implementations: RuleBased*, MLBased* — swap via config.

---

# Appendix A: Impact Identity Hash (Deterministic Dedup)

```
impact_identity_hash = SHA256(
  canonical_event_id +
  "|" + propagation_path +
  "|" + impact_type +
  "|" + str(time_horizon)
)
```

- Same event + path + type + horizon → same hash → skip duplicate

---

# Appendix B: Priority Formula (Detailed)

```
priority_score = 
  0.25 * normalize(severity, 1, 5) +
  0.25 * probability +
  0.20 * normalize(log(1 + affected_population), 0, 20) +
  0.15 * normalize(economic_weight, 0, 1e12) +
  0.15 * confidence
```

---

# Appendix C: Neo4j Schema (Future Migration)

```cypher
(:Entity {id, type, name, population, economic_weight})
(:Entity)-[:LOGISTICALLY_DEPENDS_ON {weight, confidence, valid_from, valid_to}]->(:Entity)
(:Entity)-[:ECONOMICALLY_DEPENDS_ON {weight, confidence}]->(:Entity)
(:Entity)-[:PHYSICALLY_CONNECTED_TO {weight}]->(:Entity)
(:Entity)-[:GEOGRAPHICALLY_CONTAINS]->(:Entity)
```

---

*End of Design Document*
