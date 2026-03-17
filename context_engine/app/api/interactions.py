"""Interaction tracking API."""

from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.repository import record_interaction
from app.core.cache import invalidate_feed
from app.models.interaction import InteractionCreate, InteractionResponse
from app.core.security import limiter

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/", response_model=InteractionResponse)
@limiter.limit("120/minute")
async def record_interaction_endpoint(request: Request, interaction: InteractionCreate, session: AsyncSession = Depends(get_db)):
    i = await record_interaction(
        session, interaction.user_id, interaction.event_id,
        interaction.interaction_type.value, interaction.metadata
    )
    await invalidate_feed(interaction.user_id)
    return InteractionResponse(
        user_id=i.user_id, event_id=i.event_id,
        interaction_type=i.interaction_type, created_at=i.created_at
    )
