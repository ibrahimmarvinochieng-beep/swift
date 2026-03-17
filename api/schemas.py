"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator


class SignalCreate(BaseModel):
    content: str = Field(..., min_length=20, max_length=10000)
    source_type: str = Field(..., min_length=1, max_length=50)
    source_name: str = Field(default="manual", max_length=100)
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        dangerous = ["<script>", "</script>", "javascript:"]
        for pattern in dangerous:
            v = v.replace(pattern, "")
        return v.strip()


class BatchSignalCreate(BaseModel):
    signals: List[SignalCreate] = Field(..., min_length=1, max_length=100)


class EventResponse(BaseModel):
    event_id: str
    event_type: str
    event_types: List[str] = []
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    severity: int = Field(ge=1, le=5)
    confidence_score: float = Field(ge=0, le=1)
    sources: List[str] = []
    entities: Dict[str, Any] = {}
    timestamp: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    page_size: int


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="viewer")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "analyst", "viewer"}
        if v not in allowed:
            raise ValueError(f"Role must be one of: {allowed}")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    services: Dict[str, str]


class PipelineStatsResponse(BaseModel):
    events_stored: int
    signals_ingested: int
    signals_filtered: int
    signals_rejected: int
    duplicates_caught: int
    pipeline_runs: int
    last_pipeline_run: Optional[str]
    dedup_index_size: int
    uptime_seconds: float
    collector_status: str
