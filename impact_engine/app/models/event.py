"""Event input schema for impact simulation."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re

SAFE_ID = re.compile(r"^[a-zA-Z0-9_:\-\.]+$")


class SimulateEventInput(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=128)
    source_node: str = Field(..., min_length=1, max_length=128)
    event_type: str = Field(default="disruption", min_length=1, max_length=64)
    severity: float = Field(..., ge=0, le=1)
    timestamp: datetime | None = None

    @field_validator("event_id", "source_node")
    @classmethod
    def validate_safe_id(cls, v: str) -> str:
        if not SAFE_ID.match(v):
            raise ValueError("id must contain only alphanumeric, underscore, colon, hyphen, dot")
        return v
