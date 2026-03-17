"""Graph query API endpoints."""

from typing import Optional
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel

from app.db.neo4j import get_session
from app.core.validation import validate_node_id, validate_safe_string
from app.core.cache import get_cached, set_cached
from app.core.config import get_settings
from app.services.graph_queries import (
    get_dependencies,
    get_impact_paths,
    shortest_path,
    weighted_propagation_paths,
    subgraph_by_region_or_industry,
)

router = APIRouter(tags=["queries"])


@router.get("/dependencies/{node_id}")
async def get_dependencies_endpoint(
    node_id: str = Path(..., min_length=1, max_length=128),
    max_depth: int = Query(5, ge=1, le=10),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get all dependencies of a node (multi-hop)."""
    validate_node_id(node_id)
    cache_key = f"graph:deps:{node_id}:{max_depth}:{limit}"
    cached = await get_cached(cache_key)
    if cached:
        return cached
    async with get_session() as session:
        deps = await get_dependencies(session, node_id, max_depth=max_depth, limit=limit)
    out = {"node_id": node_id, "dependencies": deps}
    await set_cached(cache_key, out, get_settings().redis_cache_ttl)
    return out


@router.get("/impact-paths/{node_id}")
async def get_impact_paths_endpoint(
    node_id: str = Path(..., min_length=1, max_length=128),
    max_depth: int = Query(5, ge=1, le=10),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get all affected entities from a node (impact propagation)."""
    validate_node_id(node_id)
    cache_key = f"graph:impact:{node_id}:{max_depth}:{limit}"
    cached = await get_cached(cache_key)
    if cached:
        return cached
    async with get_session() as session:
        paths = await get_impact_paths(session, node_id, max_depth=max_depth, limit=limit)
    out = {"node_id": node_id, "affected": paths}
    await set_cached(cache_key, out, get_settings().redis_cache_ttl)
    return out


class ShortestPathRequest(BaseModel):
    from_id: str
    to_id: str
    max_depth: int = 10


@router.get("/shortest-path")
async def shortest_path_endpoint(
    from_id: str = Query(..., min_length=1, max_length=128),
    to_id: str = Query(..., min_length=1, max_length=128),
    max_depth: int = Query(10, ge=1, le=20),
):
    """Compute shortest path between two nodes."""
    validate_node_id(from_id)
    validate_node_id(to_id)
    async with get_session() as session:
        path = await shortest_path(session, from_id, to_id, max_depth=max_depth)
    if not path:
        return {"from_id": from_id, "to_id": to_id, "path": None, "message": "No path found"}
    return {"from_id": from_id, "to_id": to_id, "path": path}


@router.get("/weighted-paths/{node_id}")
async def weighted_paths_endpoint(
    node_id: str = Path(..., min_length=1, max_length=128),
    max_depth: int = Query(5, ge=1, le=10),
    min_weight: float = Query(0.3, ge=0, le=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Compute weighted propagation paths for simulation scoring."""
    validate_node_id(node_id)
    async with get_session() as session:
        paths = await weighted_propagation_paths(
            session, node_id, max_depth=max_depth, min_weight=min_weight, limit=limit
        )
    return {"node_id": node_id, "paths": paths}


class SubgraphQuery(BaseModel):
    region: Optional[str] = None
    industry: Optional[str] = None
    limit: int = 500


@router.post("/subgraph/query")
async def subgraph_query_endpoint(query: SubgraphQuery):
    """Extract subgraph by region or industry."""
    if not query.region and not query.industry:
        return {"nodes": [], "edges": [], "message": "Provide region or industry"}
    if query.region:
        validate_safe_string(query.region)
    if query.industry:
        validate_safe_string(query.industry)
    async with get_session() as session:
        result = await subgraph_by_region_or_industry(
            session,
            region=query.region,
            industry=query.industry,
            limit=query.limit,
        )
    return result
