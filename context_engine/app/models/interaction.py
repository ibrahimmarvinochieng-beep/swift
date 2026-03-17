"""Interaction tracking model."""

from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class InteractionType(str, Enum):
    CLICK = "click"
    VIEW = "view"
    SAVE = "save"


class InteractionCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    event_id: str = Field(..., min_length=1, max_length=128)
    interaction_type: InteractionType
    metadata: dict | None = None


class InteractionResponse(BaseModel):
    user_id: str
    event_id: str
    interaction_type: str
    created_at: datetime
