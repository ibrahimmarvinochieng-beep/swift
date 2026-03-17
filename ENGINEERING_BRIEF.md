# Swift Event Intelligence Platform
## Engineering Brief — Data Ingestion & Event Detection Engine

**From:** Full-Stack Engineering, Swift AI Technologies
**To:** Project Manager
**Date:** March 16, 2026
**Status:** Phase 1 Complete — Ready for Review

---

## 1. Executive Summary

We have built and verified the first core system of the Swift platform: the **Data Ingestion & Event Detection Engine**. This is the sensory input layer — the system that listens to the world, detects real events, and converts them into structured intelligence.

**In plain terms:** Swift can now monitor news feeds, classify what happened, figure out how severe it is, and store the event — all in real time, automatically.

The system is live, tested (40/41 tests passing), and processing real data from BBC, Al Jazeera, GDACS disaster alerts, and a built-in demo feed.

---

## 2. What Has Been Built

### 2.1 Complete Pipeline (Working End-to-End)

```
Real-Time Sources → Collect → Filter Noise → AI Classify → Extract Entities
→ Geocode Location → Deduplicate → Structure → Store → Serve via API
```

Each stage is a separate module — they can be replaced, scaled, or upgraded independently.

### 2.2 Delivered Components

| Component | What It Does | Files |
|-----------|-------------|-------|
| **5 Data Collectors** | Ingest from NewsAPI, RSS (BBC/Reuters/Al Jazeera/GDACS), Twitter/X, Weather APIs, and a Demo feed | `collectors/` (7 files) |
| **Signal Filter** | Removes noise using keyword scoring + trusted-source weighting | `collectors/signal_filter.py` |
| **AI Classifier** | Detects events using Facebook BART zero-shot model + keyword hybrid fallback. Classifies into 10 event types | `services/event_detection/classifier.py` |
| **Entity Extractor** | Pulls out locations, organizations, people, dates using spaCy NLP | `services/event_detection/entity_extraction.py` |
| **Geocoder** | Converts place names → latitude/longitude via OpenStreetMap | `services/event_detection/entity_extraction.py` |
| **Deduplicator** | Prevents the same event from being stored twice using sentence embeddings + FAISS similarity search | `services/event_detection/deduplication.py` |
| **Event Structurer** | Computes severity (1-5), validates, and produces the final event object | `services/event_detection/structuring.py` |
| **Pipeline Orchestrator** | Runs the full pipeline in background threads so the API stays responsive | `pipeline/` (2 files) |
| **REST API** | 12 endpoints: auth, events CRUD, ingestion, pipeline control, metrics | `api/` (4 files) |
| **Security Layer** | JWT authentication, role-based access (admin/analyst/viewer), rate limiting, bcrypt password hashing, AES-256 encryption utilities, input sanitization | `api/auth.py`, `utils/security_utils.py` |
| **Streaming Layer** | Kafka producers/consumers + Redis Streams fallback for scaled deployments | `streaming/` (5 files) |
| **Database** | PostgreSQL schema with events, signals, users, audit log tables. SQLAlchemy async ORM models | `db/` (4 files) |
| **Monitoring** | Prometheus metrics exported at `/metrics`, structured JSON logging | `api/main.py`, `utils/logger.py` |
| **Docker** | Production Dockerfile + docker-compose (Swift + PostgreSQL + Redis + optional Kafka) | Root directory |
| **Test Suite** | 41 tests covering API, auth, RBAC, collectors, classification, structuring, dedup, pipeline | `tests/` (4 files) |

### 2.3 Verified Live Performance

| Metric | Result |
|--------|--------|
| Server startup to first HTTP response | ~3 seconds |
| API response time during background pipeline processing | Instant (non-blocking) |
| Seed cycle (65 raw signals → 21 structured events) | ~3 minutes on CPU |
| Deduplication accuracy | 28 duplicates correctly caught in first cycle |
| Event types detected | transport_disruption, natural_disaster, public_health, security_incident, infrastructure_failure, economic_event, social_unrest, technology_incident |
| Test pass rate | 40/41 (1 skipped — optional spaCy model) |

---

## 3. Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SWIFT PLATFORM (v1.0)                     │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  COLLECTORS  │  News API · RSS · Twitter · Weather · Demo   │
│              │  (async, modular, pluggable)                 │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  FILTER      │  Keyword scoring + trusted source whitelist  │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  AI ENGINE   │  BART zero-shot classifier (10 event types)  │
│              │  + keyword hybrid fallback                   │
│              │  + spaCy NER (entities, locations)            │
│              │  + Nominatim geocoding                       │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  DEDUP       │  SentenceTransformers → FAISS similarity     │
│              │  Threshold: 0.85 cosine similarity           │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  STORAGE     │  EventRepository (in-memory for dev)         │
│              │  PostgreSQL schema (production)              │
│              │  Audit logging                               │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  API         │  FastAPI · JWT · RBAC · Rate Limiting        │
│              │  12 endpoints · Swagger docs                 │
│              │  Prometheus metrics                          │
│              │                                              │
├──────────────┼──────────────────────────────────────────────┤
│              │                                              │
│  INFRA       │  Docker · Kafka · Redis · PostgreSQL         │
│              │  Thread pool for non-blocking ML inference   │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 4. Honest Assessment — What Works Well, What Doesn't Yet

### What Works Well
- **Full pipeline runs end-to-end** with real data from live sources
- **API is non-blocking** — responds instantly even during heavy ML processing
- **Deduplication is effective** — correctly identified 28 duplicate events from 49 signals
- **Security foundations are solid** — JWT, RBAC, rate limiting, encryption all in place
- **Modular design** — every component can be swapped independently
- **Zero external API keys required** — demo collector lets anyone run and test immediately

### What Needs Improvement Before Production
- **Classification runs on CPU** — BART inference takes ~3s per signal. At scale this is unacceptable
- **In-memory storage** — current dev mode loses all data on restart. PostgreSQL integration needs to be wired end-to-end
- **Single-process architecture** — works for development but won't handle high load
- **No location disambiguation** — "Paris" could mean France or Texas
- **English-only** — global events arrive in dozens of languages
- **No learning loop** — the system doesn't improve from corrections or feedback

---

## 5. Proposed Next Steps (Technical Roadmap)

### Phase 2: Production Hardening (Weeks 2-3)

| Priority | Task | Why It Matters |
|----------|------|---------------|
| **Critical** | Wire PostgreSQL end-to-end (replace in-memory store) | Data must survive restarts |
| **Critical** | GPU inference or model optimization (ONNX/quantization) | 3s/signal on CPU → <100ms on GPU |
| **Critical** | Kubernetes deployment manifests | Required for horizontal scaling |
| **High** | End-to-end encryption at rest for event data | Security requirement |
| **High** | Collector retry logic with exponential backoff | Sources go down — we need resilience |
| **High** | Per-stage latency tracking | Know exactly where time is spent |

### Phase 3: Intelligence Layer (Weeks 3-5)

| Priority | Task | Why It Matters |
|----------|------|---------------|
| **Critical** | Impact Prediction Engine | Core value proposition — "how does this affect ME?" |
| **Critical** | Personal Context Engine | User profiles, locations, interests, dependencies |
| **High** | Fine-tune classification model on event corpus | Improve from 32% to 85%+ BART accuracy |
| **High** | Multi-label classification | One event can be transport + weather + infrastructure |
| **High** | Feedback loop — human corrections retrain the model | Self-learning ability |
| **Medium** | Neo4j graph database for entity relationships | "This earthquake affects THESE supply chains" |

### Phase 4: Scale & UX (Weeks 5-8)

| Priority | Task | Why It Matters |
|----------|------|---------------|
| **Critical** | Kafka topic partitioning by region/type | Handle global event volume |
| **Critical** | Auto-scaling policies (K8s HPA) | 2 users or 1 billion — same experience |
| **High** | Real-time WebSocket push to clients | Events appear instantly, no polling |
| **High** | Multi-lingual support (translation layer) | Global events, global users |
| **Medium** | CDN + edge caching for event queries | Sub-50ms reads worldwide |
| **Medium** | Agentic Action Engine | "Your flight is affected — here are 3 alternatives" |

---

## 6. Recommendations for Improvement at This Stage

Addressing your five priorities — **security, scalability, self-learning, smooth UX, and prediction accuracy** — here's what I propose:

### 6.1 Security — "Assume we will be attacked"

**Current:** JWT + RBAC + rate limiting + bcrypt + encryption utilities.

**Proposed improvements now:**

1. **API gateway with WAF (Web Application Firewall)** — put Cloudflare or AWS WAF in front. Catches SQL injection, XSS, DDoS before they reach our code.

2. **Secret rotation** — JWT secrets and API keys should rotate automatically. Use AWS Secrets Manager or HashiCorp Vault instead of static `.env` files.

3. **Audit every action** — the `audit_log` table exists but isn't wired to every endpoint yet. Every read, write, and delete should be logged with user ID, IP, and timestamp.

4. **Zero-trust between services** — when we split into microservices, each service authenticates to every other service via mTLS (mutual TLS). No service trusts another by default.

5. **Data classification** — tag events as public, internal, or sensitive. Apply different encryption and access rules per classification.

### 6.2 Scalability — "2 users or 1 billion, same performance"

**Current:** Single-process, in-memory, thread pool for ML.

**To reach 1-billion-user scale, we need these architectural layers:**

```
Users (billions)
    │
    ▼
┌──────────┐
│ CDN/Edge │  ← Cached event reads (90% of traffic never hits our servers)
└────┬─────┘
     ▼
┌──────────┐
│ API GW   │  ← Load balancer, rate limit, auth, routing
└────┬─────┘
     ▼
┌──────────────────────┐
│ API Pods (auto-scale)│  ← 10 pods at night, 10,000 during crisis
└────┬─────────────────┘
     ▼
┌──────────┐
│ Kafka    │  ← Decouples reads from writes, buffers spikes
└────┬─────┘
     ▼
┌──────────────────────┐
│ Worker Pods (GPU)    │  ← ML inference, horizontally scaled
└────┬─────────────────┘
     ▼
┌──────────────────────────────────────┐
│ PostgreSQL (sharded) + Redis (cache) │
│ + Vector DB (embeddings)             │
│ + Neo4j (relationships)              │
└──────────────────────────────────────┘
```

**Key principle:** Stateless API servers + message queue + separate worker pools. API servers serve reads from cache. Workers process writes asynchronously. Adding more users = adding more pods. The pipeline doesn't slow down because it runs independently.

**Concrete actions now:**

1. **Add Redis caching for event reads** — 90% of API traffic is reading the same events. Cache with 30-second TTL. Eliminates database load.

2. **Database connection pooling** — use PgBouncer. Without it, 10,000 concurrent users = 10,000 database connections = crash.

3. **Kafka partitioning** — partition by geographic region. Events in Asia don't block processing of events in Europe.

4. **Stateless API** — already done. Any API pod can serve any request.

### 6.3 Self-Learning Ability — "The system gets smarter every day"

**Current:** Static models, no feedback loop.

**Proposed self-learning architecture:**

1. **Human-in-the-loop corrections** — analysts can flag "this was misclassified" via the API. Store corrections in a `feedback` table.

2. **Nightly model retraining** — collect the day's corrections, fine-tune the classifier on the corrected data, deploy updated model. Automated pipeline.

3. **Confidence calibration** — track actual accuracy vs predicted confidence. If the model says 90% confident but is wrong 40% of the time, recalibrate.

4. **Active learning** — the system identifies signals it's LEAST confident about and routes them to human analysts first. It learns fastest from its hardest cases.

5. **A/B model deployment** — run new models on 10% of traffic, compare accuracy, auto-promote the better model.

```
Events → Classify → Store with confidence
                         │
              Analyst corrects ← Feedback UI
                         │
              Corrections stored
                         │
              Nightly retrain job
                         │
              New model deployed
                         │
              A/B tested → promoted
```

### 6.4 Smooth User Experience — "It just works"

**Current:** API-only, no frontend.

**Proposed:**

1. **WebSocket real-time push** — events appear on the user's screen the moment they're detected. No refresh, no polling. Sub-second delivery.

2. **Personalized event feed** — users set their location, industry, interests. The system filters events relevant to them. A pilot in Dubai sees different events than a farmer in Kenya.

3. **Progressive loading** — show cached events instantly (from CDN), update with fresh data in the background. The UI never feels slow.

4. **Graceful degradation** — if the ML model is overloaded, fall back to keyword classification. If one collector is down, the others keep working. The user never sees an error.

5. **Latency budget** — set hard limits: API response < 200ms, event detection < 10s, notification delivery < 30s. Monitor and alert if breached.

### 6.5 Prediction Accuracy — "Trust the intelligence"

**Current:** BART zero-shot gives ~32% accuracy on event classification. Keyword fallback catches what the model misses (hybrid approach).

**Path to 90%+ accuracy:**

1. **Fine-tune on event data** — collect 10,000 labeled events (from GDACS, EM-DAT, ACLED databases). Fine-tune a DistilBERT model specifically for event classification. Expected improvement: 32% → 75%.

2. **Ensemble approach** — run 3 models (BART, fine-tuned DistilBERT, keyword), take weighted vote. Reduces individual model errors.

3. **Severity calibration** — current severity is rule-based (keyword counting). Replace with a regression model trained on historical event impact data.

4. **Location disambiguation** — use context clues: "Paris attacks" → France. "Paris weather" → could be either. Add a disambiguation model.

5. **Temporal analysis** — an earthquake report from 5 sources in 10 minutes is more credible than 1 source. Weight by corroboration.

6. **Source credibility scoring** — Reuters gets a higher trust weight than an anonymous tweet. Dynamically adjust based on historical accuracy per source.

---

## 7. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| External API rate limits/bans | High | Medium | Multiple source redundancy, API key rotation |
| Model hallucination (false events) | Medium | High | Confidence threshold + human review queue |
| Data loss on restart (current in-memory store) | High | High | **Priority: wire PostgreSQL immediately** |
| Single point of failure (one process) | High | High | **Priority: Kubernetes deployment** |
| Slow ML inference at scale | Certain | High | GPU inference + model quantization |
| Adversarial input (fake signals) | Medium | High | Source verification + anomaly detection |

---

## 8. Resource Recommendations

| Need | Justification |
|------|--------------|
| 1 GPU instance (or cloud GPU access) | ML inference is currently CPU-bound. GPU would give 30x speedup |
| PostgreSQL managed instance | Production data persistence |
| Kafka managed cluster (or Confluent Cloud) | Production-grade message streaming |
| CI/CD pipeline | Automated testing and deployment on every code change |
| Monitoring dashboard (Grafana Cloud) | Visual pipeline health for ops team |

---

## 9. Summary

The Data Ingestion & Event Detection Engine is **built, tested, and processing real-world events**. The architecture is modular and designed for the scale you described — from 2 users to 1 billion.

The immediate priorities are:
1. **PostgreSQL integration** — so data survives restarts
2. **GPU/model optimization** — so classification is fast enough for production
3. **Kubernetes deployment** — so we can scale horizontally
4. **Feedback loop** — so the system starts learning from corrections

Everything else in this brief is the path from MVP to world-scale product. The foundation is solid. The pipeline works. The next phase is about making it production-grade and intelligent.

---

*Prepared by: Engineering Team, Swift AI Technologies*
*Classification: Internal — Confidential*
