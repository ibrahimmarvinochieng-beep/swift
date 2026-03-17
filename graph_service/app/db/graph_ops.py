"""Graph write operations for nodes and edges."""

from typing import Any, Optional
from neo4j import AsyncSession

from app.models.node import NodeCreate, NodeType
from app.models.edge import EdgeCreate, RelationshipType


def _label_from_type(node_type: NodeType) -> str:
    return node_type.value


async def create_node(session: AsyncSession, node: NodeCreate) -> dict[str, Any]:
    """Create or merge a node."""
    label = _label_from_type(node.type)
    query = f"""
    MERGE (n:{label} {{id: $id}})
    ON CREATE SET
        n.type = $type,
        n.name = $name,
        n.metadata = $metadata,
        n.embedding = $embedding
    ON MATCH SET
        n.name = $name,
        n.metadata = $metadata,
        n.embedding = COALESCE($embedding, n.embedding)
    RETURN n
    """
    result = await session.run(
        query,
        id=node.id,
        type=node.type.value,
        name=node.name,
        metadata=node.metadata or {},
        embedding=node.embedding,
    )
    record = await result.single()
    n = record["n"]
    return {
        "id": n["id"],
        "type": n["type"],
        "name": n["name"],
        "metadata": n.get("metadata", {}),
        "embedding": n.get("embedding"),
    }


async def create_edge(session: AsyncSession, edge: EdgeCreate) -> Optional[dict[str, Any]]:
    """Create or merge an edge. Returns None if from/to nodes do not exist."""
    rel_type = edge.type.value
    valid_from = edge.valid_from.isoformat() if edge.valid_from else None
    valid_to = edge.valid_to.isoformat() if edge.valid_to else None

    query = f"""
    MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
    MERGE (a)-[r:{rel_type}]->(b)
    ON CREATE SET
        r.weight = $weight,
        r.confidence = $confidence,
        r.latency_hours = $latency_hours,
        r.valid_from = $valid_from,
        r.valid_to = $valid_to
    ON MATCH SET
        r.weight = $weight,
        r.confidence = $confidence,
        r.latency_hours = $latency_hours,
        r.valid_from = $valid_from,
        r.valid_to = $valid_to
    RETURN a.id as from_id, b.id as to_id, type(r) as type
    """
    result = await session.run(
        query,
        from_id=edge.from_id,
        to_id=edge.to_id,
        weight=edge.weight,
        confidence=edge.confidence,
        latency_hours=edge.latency_hours,
        valid_from=valid_from,
        valid_to=valid_to,
    )
    record = await result.single()
    if not record:
        return None
    return {
        "from_id": record["from_id"],
        "to_id": record["to_id"],
        "type": record["type"],
    }
