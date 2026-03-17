"""SQLAlchemy models."""

from datetime import datetime
from sqlalchemy import String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class UserModel(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    profession: Mapped[str] = mapped_column(String(255), default="")
    industries: Mapped[list] = mapped_column(JSON, default=list)
    alert_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    interactions = relationship("InteractionModel", back_populates="user")


class InteractionModel(Base):
    __tablename__ = "interactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), ForeignKey("users.user_id"))
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    interaction_type: Mapped[str] = mapped_column(String(32), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user = relationship("UserModel", back_populates="interactions")
