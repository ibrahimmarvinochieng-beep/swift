"""Edge/Relationship models for the Dependency Graph."""

import re
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum

SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_:\-\.]+$")


class RelationshipType(str, Enum):
    LOCATED_IN = "LOCATED_IN"
    PHYSICALLY_CONNECTED_TO = "PHYSICALLY_CONNECTED_TO"
    LOGISTICALLY_DEPENDS_ON = "LOGISTICALLY_DEPENDS_ON"
    ECONOMICALLY_DEPENDS_ON = "ECONOMICALLY_DEPENDS_ON"
    SUPPLIES = "SUPPLIES"
    SERVES = "SERVES"
    OWNED_BY = "OWNED_BY"
    ROUTES_THROUGH = "ROUTES_THROUGH"


class EdgeCreate(BaseModel):
    """Schema for creating an edge."""
    from_id: str = Field(..., min_length=1, max_length=128)
    to_id: str = Field(..., min_length=1, max_length=128)
    type: RelationshipType

    @field_validator("from_id", "to_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not SAFE_ID_PATTERN.match(v):
            raise ValueError("id must contain only alphanumeric, underscore, colon, hyphen, dot")
        return v.strip()
    weight: float = Field(..., ge=0, le=1)
    confidence: float = Field(..., ge=0, le=1)
    latency_hours: Optional[int] = Field(None, ge=0)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class EdgeResponse(BaseModel):
    """Schema for edge response."""
    from_id: str
    to_id: str
    type: str
    weight: float
    confidence: float
    latency_hours: Optional[int] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
