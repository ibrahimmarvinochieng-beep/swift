"""Node models for the Dependency Graph."""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

# Safe ID pattern: alphanumeric, underscore, colon, hyphen, dot only (prevents Cypher injection)
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_:\-\.]+$")


class NodeType(str, Enum):
    LOCATION = "Location"
    INFRASTRUCTURE = "Infrastructure"
    INDUSTRY = "Industry"
    ORGANIZATION = "Organization"
    SUPPLY_CHAIN = "SupplyChain"


class NodeCreate(BaseModel):
    """Schema for creating a node."""
    id: str = Field(..., min_length=1, max_length=128)
    type: NodeType

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not SAFE_ID_PATTERN.match(v):
            raise ValueError("id must contain only alphanumeric, underscore, colon, hyphen, dot")
        return v.strip()
    name: str = Field(..., min_length=1, max_length=255)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class NodeResponse(BaseModel):
    """Schema for node response."""
    id: str
    type: str
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True
