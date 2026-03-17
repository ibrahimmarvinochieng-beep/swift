"""Node API endpoints."""

from fastapi import APIRouter, HTTPException, Request, Path
from app.core.security import limiter
from app.core.cache import invalidate_graph_cache_on_write
from app.db.neo4j import get_session
from app.db.graph_ops import create_node as db_create_node
from app.services.graph_queries import get_node
from app.models.node import NodeCreate, NodeResponse

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("/", response_model=NodeResponse)
@limiter.limit("60/minute")
async def post_node(request: Request, node: NodeCreate):
    """Create or update a node."""
    async with get_session() as session:
        created = await db_create_node(session, node)
    await invalidate_graph_cache_on_write()
    return NodeResponse(**created)


@router.get("/{node_id}", response_model=NodeResponse)
@limiter.limit("60/minute")
async def get_node_by_id(request: Request, node_id: str = Path(..., min_length=1, max_length=128)):
    """Get a node by id."""
    from app.core.validation import validate_node_id
    validate_node_id(node_id)
    async with get_session() as session:
        node = await get_node(session, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeResponse(**node)
