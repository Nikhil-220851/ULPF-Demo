"""
SQLAlchemy ORM models for ULPF PostgreSQL persistence.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy import String, Text, Float, Boolean, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Dialect-agnostic JSON type that compiles to native JSONB in PostgreSQL and JSON in SQLite/others
JSONType = JSON().with_variant(JSONB, "postgresql")

from app.database.connection import Base

def utc_now():
    return datetime.now(timezone.utc)

class EventModel(Base):
    """
    Primary events table storing normalized OCSF Universal Events.
    Uses JSONB for complete lossless OCSF event storage while extracting
    frequently-indexed columns (event_id, timestamp, format, IPs, ports).
    """
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    detected_format: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    parser: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    raw_event: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Indexed endpoint query fields extracted from OCSF src/dst
    source_ip: Mapped[Optional[str]] = mapped_column(String(45), index=True, nullable=True)
    source_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    destination_ip: Mapped[Optional[str]] = mapped_column(String(45), index=True, nullable=True)
    destination_port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Complete OCSF v1.3.0 event JSON representation
    ocsf: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    
    # Unmapped fields JSON representation
    unmapped_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    history: Mapped["ProcessingHistoryModel"] = relationship("ProcessingHistoryModel", back_populates="event", uselist=False, cascade="all, delete-orphan")


class ProcessingHistoryModel(Base):
    """
    Processing history table recording execution pipeline metadata.
    """
    __tablename__ = "processing_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), ForeignKey("events.event_id"), unique=True, index=True, nullable=False)
    
    validation_status: Mapped[str] = mapped_column(String(32), nullable=False)
    ocsf_validation_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    
    mapping_source: Mapped[str] = mapped_column(String(32), nullable=False, default="rule")
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_status: Mapped[str] = mapped_column(String(32), default="not_applicable", nullable=False)

    # Full validation / provenance detail dictionaries
    validation_detail: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    ocsf_validation_detail: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)
    provenance: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    event: Mapped["EventModel"] = relationship("EventModel", back_populates="history")
