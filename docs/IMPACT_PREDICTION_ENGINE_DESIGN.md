# Impact Prediction Engine — Foundation Design

**Swift Event Intelligence Platform**  
**Version:** 0.1 (Design Phase)  
**Status:** Design Only — No Implementation**

---

## 1. System Architecture

### 1.1 Core Modules

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SWIFT EVENT INTELLIGENCE PLATFORM                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────────┐   │
│  │   Event      │     │              IMPACT PREDICTION ENGINE                 │   │
│  │   Detection  │────▶│                                                      │   │
│  │   Pipeline   │     │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  └──────────────┘     │  │   Event →   │  │  Dependency  │  │   Impact    │  │   │
│         │             │  │   Impact    │─▶│  Graph      │─▶│  Simulation │  │   │
│         │             │  │   Mapper    │  │  Service    │  │  Engine     │  │   │
│         │             │  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│         │             │         │                  │                  │       │   │
│         │             │         │                  │                  ▼       │   │
│         │             │         │                  │         ┌─────────────┐  │   │
│         │             │         │                  │         │   Scoring   │  │   │
│         │             │         │                  │         │   System    │  │   │
│         │             │         └──────────────────┘         └─────────────┘  │   │
│         │             │                              │                  │       │   │
│         │             │                              ▼                  ▼       │   │
│         │             │                    ┌─────────────────────────────────┐  │   │
│         │             │                    │       Impact Store              │  │   │
│         │             │                    │  (PostgreSQL + Cache)           │  │   │
│         │             │                    └─────────────────────────────────┘  │   │
│         │             └──────────────────────────────────────────────────────┘   │
│         │                                    │                                    │
│         │                                    ▼                                    │
│  ┌─────┴─────┐                    ┌─────────────────────────────────┐           │
│  │ Personal  │◀───────────────────│   Downstream Consumers           │           │
│  │ Context   │                    │   • Personal Context Engine     │           │
│  │ Engine    │                    │   • Agentic Actions Engine       │           │
│  └───────────┘                    │   • Alerting / Notifications      │           │
│  ┌──────────────┐                 │   • API / Mobile App             │           │
│  │  Agentic    │◀────────────────└─────────────────────────────────┘           │
│  │  Actions    │                                                                  │
│  └──────────────┘                                                                  │
│                                                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Module Responsibilities

| Module | Responsibility | Input | Output |
|--------|----------------|-------|--------|
| **Event → Impact Mapper** | Maps event types to impact types with rules. | Structured event | Impact hypotheses (type, probability, conditions) |
| **Dependency Graph Service** | Queries entities, relationships, dependencies. | Graph query | Affected entities, paths, dependencies |
| **Impact Simulation Engine** | Expands impacts through graph, computes ripple effects. | Event + hypotheses | Full impact tree with probabilities |
| **Scoring System** | Normalizes severity, probability, confidence, time-to-impact. | Raw impact data | Standardized scores (1–5, 0–1, etc.) |
| **Impact Store** | Persists impacts, entities, audit trail. | Impact records | Stored/retrieved impacts |

### 1.3 Data Flow (High-Level)

```
Event (from pipeline)
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 1. Event → Impact Mapper                                                         │
│    • Lookup event_type → impact_type rules                                        │
│    • Apply conditions (severity, location, infrastructure)                        │
│    • Output: initial impact hypotheses with P(impact)                              │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 2. Dependency Graph Service                                                       │
│    • Resolve event location → graph entities                                      │
│    • Find affected infrastructure, industries, supply chains                      │
│    • Output: entity graph (nodes + edges) for simulation                          │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 3. Impact Simulation Engine                                                      │
│    • Start from primary impact hypotheses                                         │
│    • Traverse graph: propagate through dependencies                                │
│    • Apply decay rules (probability decay per hop)                                │
│    • Output: impact tree with ripple effects                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 4. Scoring System                                                                 │
│    • Compute severity (1–5), probability (0–1), confidence (0–1)                  │
│    • Compute geographic spread, time-to-impact                                     │
│    • Output: standardized impact records                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 5. Impact Store                                                                   │
│    • Persist impacts, impact_entities                                             │
│    • Emit to Kafka (for Personal Context, Agentic Actions)                         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Impact Data Model

### 2.1 Core Schema (PostgreSQL)

```sql
-- =============================================================================
-- IMPACTS
-- =============================================================================
CREATE TABLE impacts (
    impact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(event_id),
    
    -- Impact classification
    impact_type VARCHAR(64) NOT NULL,  -- e.g. transport_disruption, supply_chain_delay
    impact_category VARCHAR(32) NOT NULL,  -- primary, secondary, tertiary
    
    -- Scoring (normalized)
    severity SMALLINT NOT NULL CHECK (severity BETWEEN 1 AND 5),
    probability DECIMAL(5,4) NOT NULL CHECK (probability BETWEEN 0 AND 1),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    
    -- Temporal
    time_horizon_hours VARCHAR(32),  -- immediate, short_term, medium_term, long_term
    time_horizon_min INTEGER,         -- optional numeric bounds
    time_horizon_max INTEGER,
    
    -- Geographic
    geographic_spread VARCHAR(32),   -- local, regional, national, continental, global
    affected_region VARCHAR(128),
    centroid_lat DECIMAL(10,7),
    centroid_lon DECIMAL(10,7),
    radius_km INTEGER,
    
    -- Simulation metadata
    simulation_depth INTEGER DEFAULT 0,  -- 0 = primary, 1 = first hop, etc.
    parent_impact_id UUID REFERENCES impacts(impact_id),
    propagation_path VARCHAR(255),     -- e.g. "event.location -> port -> shipping"
    
    -- Extensibility for ML
    model_version VARCHAR(32),
    raw_scores JSONB,
    features JSONB,
    
    -- Audit
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_impacts_event (event_id),
    INDEX idx_impacts_type (impact_type),
    INDEX idx_impacts_severity (severity),
    INDEX idx_impacts_created (created_at)
);

-- =============================================================================
-- IMPACT_ENTITIES (affected entities)
-- =============================================================================
CREATE TABLE impact_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    impact_id UUID NOT NULL REFERENCES impacts(impact_id),
    
    -- Entity reference
    entity_type VARCHAR(32) NOT NULL,  -- location, infrastructure, industry, organization
    entity_id VARCHAR(128) NOT NULL,   -- graph node ID or external ID
    entity_name VARCHAR(255),
    
    -- Entity metadata
    entity_metadata JSONB,
    
    -- Impact on this entity
    affected_severity SMALLINT CHECK (affected_severity BETWEEN 1 AND 5),
    affected_probability DECIMAL(5,4) CHECK (affected_probability BETWEEN 0 AND 1),
    role VARCHAR(32),  -- direct, indirect, downstream, upstream
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_impact_entities_impact (impact_id),
    INDEX idx_impact_entities_entity (entity_type, entity_id),
    UNIQUE (impact_id, entity_type, entity_id)
);

-- =============================================================================
-- IMPACT_RULES (configurable MVP rules)
-- =============================================================================
CREATE TABLE impact_rules (
    rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(64) NOT NULL,
    impact_type VARCHAR(64) NOT NULL,
    
    -- Conditions (JSON for flexibility)
    conditions JSONB NOT NULL,  -- e.g. {"min_severity": 4, "location_types": ["coastal"]}
    
    -- Output
    base_probability DECIMAL(5,4) NOT NULL,
    base_severity SMALLINT NOT NULL,
    time_horizon VARCHAR(32),
    
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,  -- higher = evaluated first
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    INDEX idx_impact_rules_event (event_type)
);

-- =============================================================================
-- IMPACT_AUDIT_LOG
-- =============================================================================
CREATE TABLE impact_audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID,
    impact_id UUID,
    action VARCHAR(32) NOT NULL,  -- created, updated, propagated
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.2 JSON Schema (Extensibility)

```json
{
  "impact": {
    "impact_id": "uuid",
    "event_id": "uuid",
    "impact_type": "string",
    "severity": 1,
    "probability": 0.85,
    "confidence": 0.8,
    "time_horizon": "short_term",
    "geographic_spread": "regional",
    "affected_entities": [
      {
        "entity_type": "infrastructure",
        "entity_id": "port-santiago",
        "affected_severity": 4,
        "affected_probability": 0.8
      }
    ],
    "raw_scores": {},
    "model_version": "rule_v1"
  }
}
```

---

## 3. Event → Impact Mapping Layer (MVP Logic)

### 3.1 Rule Structure

```yaml
# Example rule definition (YAML/JSON config)
rule:
  id: EQ-001
  event_type: natural_disaster
  impact_type: transport_disruption
  conditions:
    min_severity: 4
    location_types: [coastal, inland]
    keywords: [earthquake, tsunami]
  output:
    base_probability: 0.8
    base_severity: 4
    time_horizon: immediate
  decay:
    per_hop: 0.2  # probability *= 0.8 per dependency hop
```

### 3.2 Rule Evaluation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Event arrives                                                    │
│   event_type: natural_disaster                                   │
│   severity: 5                                                    │
│   location: Santiago, Chile (coastal)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Filter rules by event_type                                    │
│    → Match: EQ-001, EQ-002, ...                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Evaluate conditions (AND within rule)                         │
│    • severity >= 4 ? YES                                         │
│    • location in [coastal, inland] ? YES                         │
│    • keywords match ? YES                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Emit impact hypothesis                                        │
│    impact_type: transport_disruption                             │
│    probability: 0.8                                              │
│    severity: 4                                                   │
│    time_horizon: immediate                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Rule Registry (Modular)

| Component | Responsibility |
|-----------|----------------|
| **RuleLoader** | Load rules from DB/config (hot-reload capable) |
| **ConditionEvaluator** | Evaluate conditions against event (pluggable evaluators) |
| **RuleEngine** | Orchestrate: filter → evaluate → emit hypotheses |

### 3.4 Example Rule Set (Design Only)

| Event Type | Impact Type | Condition | P | Severity |
|------------|-------------|-----------|---|----------|
| natural_disaster | transport_disruption | severity ≥ 4 | 0.8 | 4 |
| natural_disaster | infrastructure_failure | severity ≥ 5, coastal | 0.9 | 5 |
| economic_event | supply_chain_delay | location in trade_region | 0.7 | 3 |
| transport_disruption | supply_chain_delay | severity ≥ 3 | 0.85 | 4 |
| public_health | travel_restriction | severity ≥ 4 | 0.75 | 4 |

---

## 4. Dependency Graph Foundation

### 4.1 Entity Types

| Entity Type | Description | Example IDs |
|-------------|-------------|-------------|
| **location** | Geographic (city, region, country) | `geo:santiago`, `geo:chile` |
| **infrastructure** | Ports, airports, roads, power grids | `infra:port-santiago`, `infra:scl` |
| **industry** | Sectors (mining, agriculture, tech) | `ind:mining`, `ind:shipping` |
| **organization** | Companies, agencies | `org:company-x` |
| **supply_chain** | Links between entities | `sc:port-export` |

### 4.2 Relationship Types

| Relationship | From | To | Meaning |
|--------------|------|-----|---------|
| **located_in** | location | location | Santiago → Chile |
| **contains** | location | infrastructure | Chile → Port of Valparaiso |
| **serves** | infrastructure | industry | Port → Mining |
| **supplies** | location | location | Chile → China (copper) |
| **depends_on** | industry | infrastructure | Mining → Port |
| **affects** | (generic) | (generic) | Impact propagation |

### 4.3 Graph Storage Options

| Option | Pros | Cons | Recommendation |
|--------|------|------|-----------------|
| **Neo4j** | Native graph, Cypher, fast traversal | Ops overhead, cost | **Preferred for graph-heavy** |
| **PostgreSQL + recursive CTEs** | Single DB, simpler | Slower for deep traversals | **MVP / hybrid** |
| **Hybrid** | PostgreSQL for impacts, Neo4j for graph | Two systems | **Scale when needed** |

**MVP Recommendation:** PostgreSQL with `graph_edges` table + recursive CTEs. Migrate to Neo4j when traversal depth > 3 or query volume > 10K/s.

### 4.4 Graph Schema (PostgreSQL MVP)

```sql
CREATE TABLE graph_entities (
    entity_id VARCHAR(128) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    name VARCHAR(255),
    metadata JSONB,
    location_id VARCHAR(128),  -- for geo entities
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE graph_edges (
    edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id VARCHAR(128) NOT NULL REFERENCES graph_entities(entity_id),
    to_entity_id VARCHAR(128) NOT NULL REFERENCES graph_entities(entity_id),
    relationship_type VARCHAR(32) NOT NULL,
    weight DECIMAL(5,4) DEFAULT 1.0,  -- for propagation
    metadata JSONB,
    UNIQUE (from_entity_id, to_entity_id, relationship_type)
);

CREATE INDEX idx_graph_edges_from ON graph_edges(from_entity_id);
CREATE INDEX idx_graph_edges_to ON graph_edges(to_entity_id);
```

### 4.5 Query Patterns (Design)

| Query | Purpose | Implementation |
|-------|---------|----------------|
| **Get entities in location** | `location:Santiago` → all infra, industries | `SELECT * FROM graph_entities WHERE location_id = ?` |
| **Get downstream dependencies** | Port → what depends on it | Recursive CTE `depends_on` |
| **Get affected by event type** | Earthquake → coastal infra | Join event_type → impact_type → entity_type |
| **Propagation path** | Event → Impact1 → Impact2 | BFS/DFS with depth limit |

---

## 5. Impact Simulation Logic

### 5.1 Simulation Flow

```
Primary Impact Hypotheses (from Mapper)
    │
    ▼
For each hypothesis:
    │
    ├─▶ Resolve affected entities (Graph: event.location → entities)
    │
    ├─▶ For each entity:
    │       ├─▶ Find outgoing edges (depends_on, supplies)
    │       ├─▶ Create secondary impact hypotheses
    │       └─▶ Apply probability decay: P_new = P_old * decay_per_hop
    │
    ├─▶ Repeat for depth N (configurable, default 2)
    │
    └─▶ Aggregate into impact tree
```

### 5.2 Probability Decay

```
Primary:  P = 0.8
Hop 1:    P = 0.8 * 0.8 = 0.64
Hop 2:    P = 0.64 * 0.8 = 0.51
```

Configurable per impact_type or rule.

### 5.3 Rule-Based (MVP) vs ML (Future)

| Aspect | MVP (Rule-Based) | Future (ML) |
|--------|------------------|-------------|
| **Input** | Event + rules + graph | Event + embeddings + graph |
| **Output** | Deterministic impact tree | Probabilistic with uncertainty |
| **Training** | N/A | Historical events + outcomes |
| **Update** | Config change | Model retrain |
| **Integration** | Same API, swap engine | Same API, swap engine |

---

## 6. Scoring System

### 6.1 Severity (1–5)

| Level | Label | Criteria |
|-------|-------|----------|
| 1 | Low | Minor disruption, localized |
| 2 | Moderate | Noticeable but contained |
| 3 | Significant | Regional impact, recovery possible |
| 4 | High | Major disruption, recovery difficult |
| 5 | Critical | Catastrophic, widespread |

**Formula (MVP):** `severity = max(base_severity, f(event_severity, geographic_spread))`

### 6.2 Probability (0–1)

- `probability` = likelihood that this impact will occur
- Combined from: rule base_probability × decay × condition confidence

### 6.3 Confidence (0–1)

- `confidence` = how confident we are in this prediction
- Factors: rule quality, data completeness, graph coverage

### 6.4 Geographic Spread

| Value | Radius (km) | Description |
|-------|-------------|-------------|
| local | < 50 | Single city |
| regional | 50–500 | Multi-city |
| national | 500–2000 | Country |
| continental | 2000+ | Multi-country |
| global | N/A | Worldwide |

### 6.5 Time-to-Impact

| Horizon | Min (h) | Max (h) |
|---------|---------|---------|
| immediate | 0 | 24 |
| short_term | 24 | 168 (1 week) |
| medium_term | 168 | 720 (30 days) |
| long_term | 720 | ∞ |

---

## 7. Integration Points

### 7.1 Input: Event Pipeline

```
Event Detection Pipeline
    │
    ├─▶ Event stored in events table
    │
    └─▶ Trigger: Kafka topic "events.raw" OR
        Trigger: DB trigger + worker poll OR
        Trigger: HTTP webhook from pipeline
```

**Recommended:** Kafka topic `events.raw` — consumer group `impact-prediction` processes events.

### 7.2 Output: Impact Store

- Write to `impacts`, `impact_entities` tables
- Emit to Kafka topic `impacts.predicted` for downstream consumers

### 7.3 Output: Downstream Consumers

| Consumer | Topic / API | Payload |
|----------|-------------|---------|
| Personal Context Engine | `impacts.predicted` | impact_id, event_id, user_id (if matched) |
| Agentic Actions Engine | `impacts.predicted` | impact + suggested actions |
| API / Mobile | `GET /api/v1/impacts?event_id=X` | Impact list |

### 7.4 API Endpoints (Design)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/events/{id}/impacts` | Fetch impacts for event |
| GET | `/api/v1/impacts/{id}` | Fetch single impact |
| GET | `/api/v1/impacts?event_id=&severity_min=` | List impacts with filters |
| POST | `/api/v1/admin/rules` | Add/update impact rule (admin) |

---

## 8. Performance & Scalability

### 8.1 Real-Time Target

- **Sub-10 seconds** per event (p95)
- Breakdown: Mapper 100ms, Graph 2s, Simulation 5s, Store 500ms

### 8.2 Horizontal Scaling

```
                    ┌─────────────────┐
                    │  Kafka          │
                    │  events.raw     │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Worker 1      │   │ Worker 2      │   │ Worker N      │
│ (consumer)    │   │ (consumer)    │   │ (consumer)    │
└───────────────────────────────┘
        │ Partition by event_id
        ▼
┌───────────────────────────────────────────────────────┐
│  Impact Prediction Engine (stateless)                  │
└───────────────────────────────────────────────────────┘
```

### 8.3 Caching

| Cache | Key | TTL | Purpose |
|-------|-----|-----|---------|
| Graph queries | `graph:location:{id}` | 1h | Entity lookup by location |
| Rule set | `rules:impact` | 5m | Hot-reload rules |
| Impact by event | `impacts:event:{id}` | 10m | Avoid repeated computation |

### 8.4 Global Scale

- **Event volume:** 1M events/day → ~12 events/sec average
- **Burst:** 100 events/sec (design for 10x)
- **Workers:** 10–50 consumers, scale with Kafka partitions

---

## 9. Security Considerations

### 9.1 Data Validation

- Input events: schema validation (Pydantic), max size limits
- Reject malicious payloads (e.g. oversized, injection attempts)

### 9.2 Fake Event Protection

- Source attestation (API key, signed payload)
- Rate limiting per source
- Anomaly detection for impossible events (future)

### 9.3 Access Control

- Impact data: RBAC — viewers see impacts, analysts see rules
- Admin: rule CRUD, graph management
- Audit: all impact creations logged

### 9.4 Audit Logging

- `impact_audit_log`: event_id, impact_id, action, timestamp
- Retain for compliance (configurable retention)

---

## 10. Implementation Roadmap (Modular)

### Phase 1: Foundation
1. Create `impacts`, `impact_entities`, `impact_rules` tables
2. Implement RuleLoader + ConditionEvaluator
3. Implement Event → Impact Mapper (rule-based only)

### Phase 2: Graph
4. Create `graph_entities`, `graph_edges` tables
5. Seed with initial geographic + infrastructure data
6. Implement Dependency Graph Service (recursive CTE)

### Phase 3: Simulation
7. Implement Impact Simulation Engine

### Phase 4: Integration
8. Kafka consumer for events
9. API endpoints
10. Downstream topic emission

### Phase 5: Scale
11. Caching layer
12. Neo4j migration (if needed)
13. ML model integration (future)

---

## Appendix A: ASCII Diagram — Full Flow

```
                    ┌─────────────────┐
                    │  Structured     │
                    │  Event          │
                    └────────┬────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ EVENT → IMPACT MAPPER                                                           │
│   Rules: event_type + conditions → impact hypotheses                            │
└────────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ DEPENDENCY GRAPH SERVICE                                                       │
│   event.location → graph_entities → graph_edges                                 │
└────────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ IMPACT SIMULATION ENGINE                                                       │
│   Hypotheses → traverse graph → propagate → decay → impact tree                 │
└────────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ SCORING SYSTEM                                                                  │
│   severity, probability, confidence, time_horizon, geographic_spread            │
└────────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ IMPACT STORE                                                                    │
│   PostgreSQL → Kafka (impacts.predicted)                                        │
└────────────────────────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Personal        │ │ Agentic         │ │ API / Mobile     │
│ Context Engine  │ │ Actions Engine  │ │                  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Impact** | Predicted real-world consequence of an event |
| **Impact hypothesis** | Initial rule-based prediction before graph expansion |
| **Impact tree** | Hierarchical structure of primary + ripple effects |
| **Ripple effect** | Secondary/tertiary impact propagated through dependencies |
| **Time horizon** | When the impact is expected to occur |
| **Geographic spread** | Spatial extent of the impact |
