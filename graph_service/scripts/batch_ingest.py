"""Batch ingestion: ETL -> Normalize -> Create Nodes -> Create Edges -> Neo4j."""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import AsyncGraphDatabase
from app.core.config import get_settings
from app.models.node import NodeCreate, NodeType
from app.models.edge import EdgeCreate, RelationshipType
from datetime import datetime


async def load_json_sample(path: str) -> list[dict]:
    """Load sample data from JSON file."""
    p = Path(path)
    if not p.exists():
        return []
    with open(p) as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


async def create_nodes_batch(driver, nodes: list[NodeCreate], batch_size: int = 500):
    """Batch create nodes in Neo4j."""
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i : i + batch_size]
        async with driver.session() as session:
            await session.execute_write(_write_nodes, batch)
        print(f"Created nodes batch {i // batch_size + 1}")


async def _write_nodes(tx, batch: list[NodeCreate]):
    for node in batch:
        await tx.run(
            f"""
            MERGE (n:{node.type.value} {{id: $id}})
            ON CREATE SET n.type=$type, n.name=$name, n.metadata=$metadata
            ON MATCH SET n.name=$name, n.metadata=$metadata
            """,
            id=node.id,
            type=node.type.value,
            name=node.name,
            metadata=node.metadata or {},
        )


async def create_edges_batch(driver, edges: list[EdgeCreate], batch_size: int = 500):
    """Batch create edges in Neo4j."""
    for i in range(0, len(edges), batch_size):
        batch = edges[i : i + batch_size]
        async with driver.session() as session:
            await session.execute_write(_write_edges, batch)
        print(f"Created edges batch {i // batch_size + 1}")


async def _write_edges(tx, batch: list[EdgeCreate]):
    for edge in batch:
        await tx.run(
            f"""
            MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
            MERGE (a)-[r:{edge.type.value}]->(b)
            SET r.weight=$weight, r.confidence=$confidence, r.latency_hours=$latency_hours
            """,
            from_id=edge.from_id,
            to_id=edge.to_id,
            weight=edge.weight,
            confidence=edge.confidence,
            latency_hours=edge.latency_hours or 0,
        )


def normalize_osm_infrastructure(raw: list[dict]) -> tuple[list[NodeCreate], list[EdgeCreate]]:
    """Normalize OpenStreetMap-style infrastructure data."""
    nodes = []
    edges = []
    seen = set()
    for item in raw:
        nid = item.get("id") or f"infra:{item.get('osm_id', item.get('name', 'unknown'))}"
        if nid in seen:
            continue
        seen.add(nid)
        nodes.append(
            NodeCreate(
                id=nid,
                type=NodeType.INFRASTRUCTURE,
                name=item.get("name", nid),
                metadata={"source": "osm", **{k: v for k, v in item.items() if k not in ("id", "name")}},
            )
        )
        loc = item.get("location") or item.get("loc_id")
        if loc:
            edges.append(
                EdgeCreate(
                    from_id=nid,
                    to_id=loc if isinstance(loc, str) else f"loc:{loc}",
                    type=RelationshipType.LOCATED_IN,
                    weight=1.0,
                    confidence=0.95,
                )
            )
    return nodes, edges


def normalize_trade_data(raw: list[dict]) -> tuple[list[NodeCreate], list[EdgeCreate]]:
    """Normalize trade/economic data."""
    nodes = []
    edges = []
    for item in raw:
        from_id = item.get("from") or item.get("exporter") or f"org:{item.get('from_id', 'unknown')}"
        to_id = item.get("to") or item.get("importer") or f"org:{item.get('to_id', 'unknown')}"
        nodes.append(
            NodeCreate(
                id=from_id,
                type=NodeType.ORGANIZATION,
                name=item.get("from_name", from_id),
                metadata={"source": "trade"},
            )
        )
        nodes.append(
            NodeCreate(
                id=to_id,
                type=NodeType.ORGANIZATION,
                name=item.get("to_name", to_id),
                metadata={"source": "trade"},
            )
        )
        edges.append(
            EdgeCreate(
                from_id=from_id,
                to_id=to_id,
                type=RelationshipType.SUPPLIES,
                weight=float(item.get("weight", 0.8)),
                confidence=float(item.get("confidence", 0.85)),
                latency_hours=int(item.get("latency_hours", 0)),
            )
        )
    return nodes, edges


async def run_ingest(data_dir: str = "data"):
    """Run full batch ingestion pipeline."""
    settings = get_settings()
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    all_nodes = []
    all_edges = []
    data_path = Path(data_dir)
    if data_path.exists():
        for f in data_path.glob("**/*.json"):
            raw = await load_json_sample(str(f))
            if "osm" in f.name or "infrastructure" in f.name:
                n, e = normalize_osm_infrastructure(raw)
            else:
                n, e = normalize_trade_data(raw)
            all_nodes.extend(n)
            all_edges.extend(e)
    if not all_nodes and not all_edges:
        # Seed with minimal sample
        all_nodes = [
            NodeCreate(id="loc:tr", type=NodeType.LOCATION, name="Turkey", metadata={}),
            NodeCreate(id="infra:airport_ist", type=NodeType.INFRASTRUCTURE, name="Istanbul Airport", metadata={}),
            NodeCreate(id="ind:tourism_tr", type=NodeType.INDUSTRY, name="Tourism Turkey", metadata={}),
        ]
        all_edges = [
            EdgeCreate(from_id="infra:airport_ist", to_id="loc:tr", type=RelationshipType.LOCATED_IN, weight=1.0, confidence=1.0),
            EdgeCreate(from_id="infra:airport_ist", to_id="ind:tourism_tr", type=RelationshipType.SERVES, weight=0.9, confidence=0.95),
        ]
    await create_nodes_batch(driver, all_nodes)
    await create_edges_batch(driver, all_edges)
    await driver.close()
    print(f"Ingested {len(all_nodes)} nodes, {len(all_edges)} edges")


if __name__ == "__main__":
    asyncio.run(run_ingest())
