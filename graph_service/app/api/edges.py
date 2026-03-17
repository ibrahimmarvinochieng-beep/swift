"""Edge API endpoints."""

from fastapi import APIRouter, HTTPException, Request
from app.core.security import limiter
from app.core.cache import invalidate_graph_cache_on_write
from app.db.neo4j import get_session
from app.db.graph_ops import create_edge as db_create_edge
from app.models.edge import EdgeCreate, EdgeResponse

router = APIRouter(prefix="/edges", tags=["edges"])


@router.post("/", response_model=EdgeResponse)
@limiter.limit("60/minute")
async def post_edge(request: Request, edge: EdgeCreate):
    """Create or update an edge."""
    async with get_session() as session:
        created = await db_create_edge(session, edge)
    if created:
        await invalidate_graph_cache_on_write()
    if not created:
        raise HTTPException(
            status_code=404,
            detail="Source or target node not found",
        )
    return EdgeResponse(
        from_id=created["from_id"],
        to_id=created["to_id"],
        type=created["type"],
        weight=edge.weight,
        confidence=edge.confidence,
        latency_hours=edge.latency_hours,
        valid_from=edge.valid_from.isoformat() if edge.valid_from else None,
        valid_to=edge.valid_to.isoformat() if edge.valid_to else None,
    )
