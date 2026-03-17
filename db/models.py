import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime, ARRAY, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class Event(Base):
    __tablename__ = "events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    severity = Column(Integer)
    confidence_score = Column(Float)
    sources = Column(ARRAY(String))
    raw_text = Column(Text)
    entities = Column(JSON, default=dict)
    embedding_id = Column(String)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RawSignal(Base):
    __tablename__ = "raw_signals"

    signal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String, nullable=False, index=True)
    source_name = Column(String)
    content = Column(Text, nullable=False)
    url = Column(String)
    fetched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed = Column(Boolean, default=False)


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_log"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))
    action = Column(String, nullable=False)
    resource = Column(String)
    details = Column(JSON)
    ip_address = Column(String)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
