"""Core graph queries for dependency and impact analysis."""

from typing import Any, Optional
from neo4j import AsyncSession

from app.core.config import get_settings


async def get_node(session: AsyncSession, node_id: str) -> Optional[dict[str, Any]]:
    """Get a single node by id (searches all labels)."""
    result = await session.run(
        "MATCH (n {id: $id}) RETURN n",
        id=node_id,
    )
    record = await result.single()
    if not record:
        return None
    node = record["n"]
    return {
        "id": node["id"],
        "type": node["type"],
        "name": node["name"],
        "metadata": node.get("metadata", {}),
        "embedding": node.get("embedding"),
    }


async def get_dependencies(
    session: AsyncSession,
    node_id: str,
    max_depth: int = 5,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get all dependencies of a node (multi-hop, outgoing)."""
    settings = get_settings()
    depth = min(max_depth, settings.max_traversal_depth)
    query = f"""
    MATCH path = (start {{id: $id}})-[*1..{depth}]->(dep)
    WHERE dep.id IS NOT NULL
    WITH dep, length(path) as hop
    RETURN DISTINCT dep.id as id, dep.type as type, dep.name as name, hop
    ORDER BY hop, dep.id
    LIMIT $limit
    """
    result = await session.run(query, id=node_id, limit=limit)
    return [dict(record) async for record in result]


async def get_impact_paths(
    session: AsyncSession,
    node_id: str,
    max_depth: int = 5,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Get all affected entities from a node (impact propagation, incoming + outgoing)."""
    settings = get_settings()
    depth = min(max_depth, settings.max_traversal_depth)
    query = f"""
    MATCH path = (start {{id: $id}})-[*1..{depth}]-(affected)
    WHERE affected.id IS NOT NULL AND affected <> start
    WITH affected, length(path) as hop
    RETURN DISTINCT affected.id as id, affected.type as type, affected.name as name, hop
    ORDER BY hop, affected.id
    LIMIT $limit
    """
    result = await session.run(query, id=node_id, limit=limit)
    return [dict(record) async for record in result]


async def shortest_path(
    session: AsyncSession,
    from_id: str,
    to_id: str,
    max_depth: int = 10,
) -> Optional[list[dict[str, Any]]]:
    """Compute shortest path between two nodes."""
    settings = get_settings()
    depth = min(max_depth, settings.max_traversal_depth)
    query = f"""
    MATCH path = shortestPath(
        (a {{id: $from_id}})-[*1..{depth}]-(b {{id: $to_id}})
    )
    WITH nodes(path) as nodes, relationships(path) as rels
    UNWIND range(0, size(nodes)-1) as i
    WITH nodes[i] as n, CASE WHEN i < size(rels) THEN rels[i] ELSE null END as r
    RETURN n.id as node_id, n.name as name, type(r) as rel_type
    """
    result = await session.run(query, from_id=from_id, to_id=to_id)
    records = [dict(r) async for r in result]
    return records if records else None


async def weighted_propagation_paths(
    session: AsyncSession,
    node_id: str,
    max_depth: int = 5,
    min_weight: float = 0.3,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Compute weighted propagation paths for simulation scoring."""
    settings = get_settings()
    depth = min(max_depth, settings.max_traversal_depth)
    query = f"""
    MATCH path = (start {{id: $id}})-[r*1..{depth}]->(target)
    WHERE ALL(rel IN relationships(path) WHERE rel.weight >= $min_weight)
    WITH path,
         reduce(score = 1.0, rel IN relationships(path) | score * rel.weight * rel.confidence) as propagation_score
    WHERE propagation_score >= $min_weight
    UNWIND nodes(path) as n
    WITH path, propagation_score, collect(DISTINCT n.id) as node_ids
    RETURN node_ids, propagation_score
    ORDER BY propagation_score DESC
    LIMIT $limit
    """
    result = await session.run(
        query,
        id=node_id,
        min_weight=min_weight,
        limit=limit,
    )
    return [dict(record) async for record in result]


async def propagation_paths_with_edges(
    session: AsyncSession,
    node_id: str,
    max_depth: int = 3,
    min_weight: float = 0.0,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    """Return propagation paths with full edge details (weight, confidence, latency_hours) for impact simulation."""
    settings = get_settings()
    depth = min(max_depth, settings.max_traversal_depth)
    query = f"""
    MATCH path = (start {{id: $id}})-[r*1..{depth}]->(target)
    WHERE size(relationships(path)) > 0
    WITH path, relationships(path) as rels
    WITH path, rels,
         reduce(lat = 0, rel IN rels | lat + COALESCE(rel.latency_hours, 0)) as total_latency,
         reduce(w = 1.0, rel IN rels | w * COALESCE(rel.weight, 0.5)) as cum_weight,
         reduce(c = 1.0, rel IN rels | c * COALESCE(rel.confidence, 0.8)) as cum_confidence
    WITH path, rels, total_latency, cum_weight, cum_confidence
    UNWIND range(0, size(rels)-1) as i
    WITH path, total_latency, cum_weight, cum_confidence,
         rels[i] as rel, nodes(path)[i] as from_n, nodes(path)[i+1] as to_n
    WITH path, total_latency, cum_weight, cum_confidence,
         collect({{from_id: from_n.id, to_id: to_n.id, weight: COALESCE(rel.weight, 0.5),
                  confidence: COALESCE(rel.confidence, 0.8), latency_hours: COALESCE(rel.latency_hours, 0)}}) as edges
    RETURN [n IN nodes(path) | n.id] as node_ids, edges, total_latency, cum_weight, cum_confidence
    ORDER BY cum_weight * cum_confidence DESC
    LIMIT $limit
    """
    result = await session.run(
        query,
        id=node_id,
        min_weight=min_weight,
        limit=limit,
    )
    return [dict(record) async for record in result]


async def subgraph_by_region_or_industry(
    session: AsyncSession,
    region: Optional[str] = None,
    industry: Optional[str] = None,
    limit: int = 500,
) -> dict[str, Any]:
    """Extract subgraph by region (Location name) or industry (Industry name)."""
    nodes = []
    edges = []
    if region:
        query = """
        MATCH (loc:Location {name: $region})
        OPTIONAL MATCH (loc)-[r]-(n)
        WITH loc, r, n
        WHERE n IS NOT NULL
        WITH collect(DISTINCT loc) + collect(DISTINCT n) as all_nodes, collect(DISTINCT r) as all_rels
        UNWIND all_nodes as node
        WITH collect(DISTINCT node) as node_list, [rel IN all_rels WHERE rel IS NOT NULL] as rel_list
        UNWIND node_list as n
        WITH n, rel_list
        RETURN n
        LIMIT $limit
        """
        result = await session.run(query, region=region, limit=limit)
        nodes = [
            {"id": r["n"]["id"], "type": r["n"]["type"], "name": r["n"]["name"]}
            async for r in result
        ]
        # Get edges for these nodes
        if nodes:
            ids = [n["id"] for n in nodes]
            edge_result = await session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.id IN $ids AND b.id IN $ids
                RETURN a.id as from_id, b.id as to_id, type(r) as type, r.weight as weight
                LIMIT $limit
                """,
                ids=ids,
                limit=limit,
            )
            edges = [dict(e) async for e in edge_result]
    if industry:
        query = """
        MATCH (ind:Industry {name: $industry})
        OPTIONAL MATCH (ind)-[r]-(n)
        WITH ind, r, n
        WHERE n IS NOT NULL
        WITH collect(DISTINCT ind) + collect(DISTINCT n) as all_nodes, collect(DISTINCT r) as all_rels
        UNWIND all_nodes as node
        WITH collect(DISTINCT node) as node_list
        UNWIND node_list as n
        RETURN n
        LIMIT $limit
        """
        result = await session.run(query, industry=industry, limit=limit)
        nodes = [
            {"id": r["n"]["id"], "type": r["n"]["type"], "name": r["n"]["name"]}
            async for r in result
        ]
        if nodes:
            ids = [n["id"] for n in nodes]
            edge_result = await session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.id IN $ids AND b.id IN $ids
                RETURN a.id as from_id, b.id as to_id, type(r) as type, r.weight as weight
                LIMIT $limit
                """,
                ids=ids,
                limit=limit,
            )
            edges = [dict(e) async for e in edge_result]
    return {"nodes": nodes, "edges": edges}
