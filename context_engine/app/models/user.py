"""User context model."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    locations: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    profession: str = ""
    industries: list[str] = Field(default_factory=list)
    alert_preferences: dict[str, Any] = Field(default_factory=dict)


class UserUpdate(BaseModel):
    locations: list[str] | None = None
    interests: list[str] | None = None
    profession: str | None = None
    industries: list[str] | None = None
    alert_preferences: dict[str, Any] | None = None


class UserResponse(BaseModel):
    user_id: str
    locations: list[str]
    interests: list[str]
    profession: str
    industries: list[str]
    alert_preferences: dict[str, Any]
    created_at: datetime
