"""Impact Prediction Store — SQLite persistence for impacts, graph, rules, outcomes.

Uses same data/swift.db as EventRepository. Tables: impacts, impact_entities,
impact_rules, graph_entities, graph_edges, explanations, impact_outcomes.
"""

import hashlib
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from utils.logger import logger

_DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "swift.db")


def _impact_identity_hash(event_id: str, propagation_path: str, impact_type: str, time_horizon: str) -> str:
    """Deterministic hash for impact deduplication."""
    payload = f"{event_id}|{propagation_path}|{impact_type}|{time_horizon}"
    return hashlib.sha256(payload.encode()).hexdigest()


class ImpactStore:
    """Thread-safe store for Impact Prediction Engine."""

    def __init__(self, db_path: str = _DEFAULT_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._create_tables()
        self._seed_default_rules()
        self._seed_minimal_graph()
        logger.info("impact_store_opened", path=db_path)

    def _create_tables(self):
        with self._conn:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS impacts (
                    impact_id TEXT PRIMARY KEY,
                    impact_identity_hash TEXT UNIQUE NOT NULL,
                    event_id TEXT NOT NULL,
                    impact_type TEXT NOT NULL,
                    impact_category TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    probability REAL NOT NULL,
                    confidence REAL NOT NULL,
                    time_horizon TEXT,
                    geographic_spread TEXT,
                    affected_region TEXT,
                    simulation_depth INTEGER DEFAULT 0,
                    parent_impact_id TEXT,
                    propagation_path TEXT,
                    explanation_id TEXT,
                    priority_score REAL,
                    tags TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS impact_entities (
                    id TEXT PRIMARY KEY,
                    impact_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    entity_name TEXT,
                    affected_severity INTEGER,
                    affected_probability REAL,
                    role TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (impact_id) REFERENCES impacts(impact_id)
                );

                CREATE TABLE IF NOT EXISTS impact_rules (
                    rule_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    impact_type TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    base_probability REAL NOT NULL,
                    base_severity INTEGER NOT NULL,
                    time_horizon TEXT,
                    enabled INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS graph_entities (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    name TEXT,
                    location_id TEXT,
                    population INTEGER,
                    economic_weight REAL,
                    metadata TEXT,
                    created_at TEXT
                );

                CREATE TABLE IF NOT EXISTS graph_edges (
                    edge_id TEXT PRIMARY KEY,
                    from_entity_id TEXT NOT NULL,
                    to_entity_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    weight REAL NOT NULL,
                    confidence REAL NOT NULL,
                    metadata TEXT,
                    created_at TEXT,
                    FOREIGN KEY (from_entity_id) REFERENCES graph_entities(entity_id),
                    FOREIGN KEY (to_entity_id) REFERENCES graph_entities(entity_id)
                );

                CREATE TABLE IF NOT EXISTS explanations (
                    explanation_id TEXT PRIMARY KEY,
                    impact_id TEXT NOT NULL,
                    narrative TEXT NOT NULL,
                    reasoning_path TEXT NOT NULL,
                    rule_ids TEXT,
                    created_at TEXT,
                    FOREIGN KEY (impact_id) REFERENCES impacts(impact_id)
                );

                CREATE TABLE IF NOT EXISTS impact_outcomes (
                    outcome_id TEXT PRIMARY KEY,
                    impact_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    occurred INTEGER NOT NULL,
                    occurred_at TEXT,
                    source TEXT,
                    created_at TEXT,
                    FOREIGN KEY (impact_id) REFERENCES impacts(impact_id)
                );

                CREATE INDEX IF NOT EXISTS idx_impacts_event ON impacts(event_id);
                CREATE INDEX IF NOT EXISTS idx_impacts_hash ON impacts(impact_identity_hash);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_from ON graph_edges(from_entity_id);
                CREATE INDEX IF NOT EXISTS idx_graph_edges_to ON graph_edges(to_entity_id);
            """)

    def _seed_default_rules(self):
        """Seed default event_type → impact_type rules."""
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) FROM impact_rules")
            if cur.fetchone()[0] > 0:
                return
        rules = [
            ("natural_disaster", "transport_disruption", '{"min_severity": 4}', 0.8, 4, "immediate"),
            ("natural_disaster", "infrastructure_failure", '{"min_severity": 5}', 0.9, 5, "immediate"),
            ("economic_event", "supply_chain_delay", '{"min_severity": 3}', 0.7, 3, "short_term"),
            ("transport_disruption", "supply_chain_delay", '{"min_severity": 3}', 0.85, 4, "short_term"),
            ("public_health", "travel_restriction", '{"min_severity": 4}', 0.75, 4, "short_term"),
        ]
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            for event_type, impact_type, conditions, prob, sev, horizon in rules:
                rid = str(uuid.uuid4())
                self._conn.execute(
                    """INSERT INTO impact_rules (rule_id, event_type, impact_type, conditions, base_probability, base_severity, time_horizon, enabled, priority, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 1, 0, ?)""",
                    (rid, event_type, impact_type, conditions, prob, sev, horizon, now),
                )
            self._conn.commit()

    def _seed_minimal_graph(self):
        """Seed minimal graph for demo (Chile earthquake -> port -> shipping)."""
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) FROM graph_entities")
            if cur.fetchone()[0] > 0:
                return
        entities = [
            ("geo:santiago", "location", "Santiago, Chile", "geo:chile", 7000000, 1e11, "{}"),
            ("geo:chile", "location", "Chile", None, 19000000, 3e11, "{}"),
            ("infra:port-valparaiso", "infrastructure", "Port of Valparaiso", "geo:chile", None, 5e9, "{}"),
            ("ind:copper-export", "industry", "Copper Export", None, None, 2e10, "{}"),
        ]
        edges = [
            ("geo:santiago", "geo:chile", "geographically_contains", 1.0, 1.0),
            ("geo:chile", "infra:port-valparaiso", "contains", 1.0, 1.0),
            ("infra:port-valparaiso", "geo:chile", "located_in", 1.0, 1.0),
            ("ind:copper-export", "infra:port-valparaiso", "logistically_depends_on", 0.9, 0.9),
        ]
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            for eid, etype, name, loc, pop, econ, meta in entities:
                self._conn.execute(
                    """INSERT INTO graph_entities (entity_id, entity_type, name, location_id, population, economic_weight, metadata, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (eid, etype, name, loc, pop, econ, meta, now),
                )
            for f, t, rel, w, c in edges:
                eid = str(uuid.uuid4())
                self._conn.execute(
                    """INSERT INTO graph_edges (edge_id, from_entity_id, to_entity_id, relationship_type, weight, confidence, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (eid, f, t, rel, w, c, now),
                )
            self._conn.commit()

    def get_rules_for_event_type(self, event_type: str) -> List[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT rule_id, impact_type, conditions, base_probability, base_severity, time_horizon FROM impact_rules WHERE event_type=? AND enabled=1 ORDER BY priority DESC",
                (event_type,),
            )
            return [
                {
                    "rule_id": r[0],
                    "impact_type": r[1],
                    "conditions": json.loads(r[2]),
                    "base_probability": r[3],
                    "base_severity": r[4],
                    "time_horizon": r[5],
                }
                for r in cur.fetchall()
            ]

    def get_entities_in_location(self, location: str) -> List[dict]:
        """Get entities that match location (substring or location_id)."""
        loc_lower = (location or "").lower()
        with self._lock:
            cur = self._conn.execute(
                "SELECT entity_id, entity_type, name, location_id, population, economic_weight FROM graph_entities"
            )
            rows = cur.fetchall()
        return [
            {"entity_id": r[0], "entity_type": r[1], "name": r[2], "location_id": r[3], "population": r[4], "economic_weight": r[5]}
            for r in rows
            if loc_lower in (r[2] or "").lower() or loc_lower in (r[3] or "").lower()
        ]

    def get_outgoing_edges(self, entity_id: str) -> List[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT edge_id, to_entity_id, relationship_type, weight, confidence FROM graph_edges WHERE from_entity_id=?",
                (entity_id,),
            )
            return [
                {"edge_id": r[0], "to_entity_id": r[1], "relationship_type": r[2], "weight": r[3], "confidence": r[4]}
                for r in cur.fetchall()
            ]

    def get_entity(self, entity_id: str) -> Optional[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT entity_id, entity_type, name, location_id, population, economic_weight FROM graph_entities WHERE entity_id=?",
                (entity_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        return {"entity_id": row[0], "entity_type": row[1], "name": row[2], "location_id": row[3], "population": row[4], "economic_weight": row[5]}

    def impact_exists_by_hash(self, h: str) -> bool:
        with self._lock:
            cur = self._conn.execute("SELECT 1 FROM impacts WHERE impact_identity_hash=?", (h,))
            return cur.fetchone() is not None

    def add_impact(
        self,
        event_id: str,
        impact_type: str,
        impact_category: str,
        severity: int,
        probability: float,
        confidence: float,
        time_horizon: str,
        geographic_spread: str,
        affected_region: str,
        simulation_depth: int,
        parent_impact_id: Optional[str],
        propagation_path: str,
        explanation_id: Optional[str],
        priority_score: Optional[float],
        tags: Optional[List[str]],
    ) -> Optional[str]:
        impact_id = str(uuid.uuid4())
        identity_hash = _impact_identity_hash(event_id, propagation_path or "", impact_type, time_horizon or "")
        if self.impact_exists_by_hash(identity_hash):
            return None
        now = datetime.now(timezone.utc).isoformat()
        tags_json = json.dumps(tags or [])
        with self._lock:
            self._conn.execute(
                """INSERT INTO impacts (impact_id, impact_identity_hash, event_id, impact_type, impact_category, severity, probability, confidence,
                   time_horizon, geographic_spread, affected_region, simulation_depth, parent_impact_id, propagation_path, explanation_id, priority_score, tags, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (impact_id, identity_hash, event_id, impact_type, impact_category, severity, probability, confidence,
                 time_horizon, geographic_spread, affected_region, simulation_depth, parent_impact_id, propagation_path, explanation_id, priority_score, tags_json, now),
            )
            self._conn.commit()
        return impact_id

    def add_impact_entity(self, impact_id: str, entity_type: str, entity_id: str, entity_name: str, affected_severity: int, affected_probability: float, role: str):
        eid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT INTO impact_entities (id, impact_id, entity_type, entity_id, entity_name, affected_severity, affected_probability, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (eid, impact_id, entity_type, entity_id, entity_name, affected_severity, affected_probability, role, now),
            )
            self._conn.commit()

    def update_impact_explanation(self, impact_id: str, explanation_id: str) -> bool:
        """Set explanation_id on impact."""
        with self._lock:
            cur = self._conn.execute("UPDATE impacts SET explanation_id=? WHERE impact_id=?", (explanation_id, impact_id))
            self._conn.commit()
            return cur.rowcount > 0

    def add_explanation(self, impact_id: str, narrative: str, reasoning_path: List[dict], rule_ids: Optional[List[str]]) -> str:
        ex_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        rules_json = json.dumps(rule_ids or [])
        path_json = json.dumps(reasoning_path)
        with self._lock:
            self._conn.execute(
                "INSERT INTO explanations (explanation_id, impact_id, narrative, reasoning_path, rule_ids, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (ex_id, impact_id, narrative, path_json, rules_json, now),
            )
            self._conn.commit()
        return ex_id

    def list_impacts_for_event(self, event_id: str, limit: int = 50) -> List[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT impact_id, impact_type, severity, probability, confidence, time_horizon, propagation_path, priority_score, explanation_id FROM impacts WHERE event_id=? ORDER BY COALESCE(priority_score, 0) DESC, severity DESC LIMIT ?",
                (event_id, limit),
            )
            rows = cur.fetchall()
        return [
            {
                "impact_id": r[0],
                "impact_type": r[1],
                "severity": r[2],
                "probability": r[3],
                "confidence": r[4],
                "time_horizon": r[5],
                "propagation_path": r[6],
                "priority_score": r[7],
                "explanation_id": r[8],
            }
            for r in rows
        ]

    def get_impact(self, impact_id: str) -> Optional[dict]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT impact_id, impact_identity_hash, event_id, impact_type, impact_category, severity, probability, confidence, time_horizon, geographic_spread, affected_region, simulation_depth, parent_impact_id, propagation_path, explanation_id, priority_score, tags, created_at FROM impacts WHERE impact_id=?",
                (impact_id,),
            )
            row = cur.fetchone()
        if not row:
            return None
        cols = ["impact_id", "impact_identity_hash", "event_id", "impact_type", "impact_category", "severity", "probability", "confidence", "time_horizon", "geographic_spread", "affected_region", "simulation_depth", "parent_impact_id", "propagation_path", "explanation_id", "priority_score", "tags", "created_at"]
        return dict(zip(cols, row))

    def get_explanation(self, explanation_id: str) -> Optional[dict]:
        with self._lock:
            cur = self._conn.execute("SELECT explanation_id, impact_id, narrative, reasoning_path, rule_ids FROM explanations WHERE explanation_id=?", (explanation_id,))
            row = cur.fetchone()
        if not row:
            return None
        return {
            "explanation_id": row[0],
            "impact_id": row[1],
            "narrative": row[2],
            "reasoning_path": json.loads(row[3] or "[]"),
            "rule_ids": json.loads(row[4] or "[]"),
        }

    def add_outcome(self, impact_id: str, event_id: str, occurred: bool, source: Optional[str] = None) -> str:
        oid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._conn.execute(
                "INSERT INTO impact_outcomes (outcome_id, impact_id, event_id, occurred, occurred_at, source, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (oid, impact_id, event_id, 1 if occurred else 0, now if occurred else None, source, now),
            )
            self._conn.commit()
        return oid

    def close(self):
        self._conn.close()
        logger.info("impact_store_closed", path=self._path)


_impact_store: Optional[ImpactStore] = None


def get_impact_store() -> ImpactStore:
    global _impact_store
    if _impact_store is None:
        db_path = os.environ.get("SQLITE_DB_PATH", _DEFAULT_PATH)
        _impact_store = ImpactStore(db_path=db_path or _DEFAULT_PATH)
    return _impact_store
