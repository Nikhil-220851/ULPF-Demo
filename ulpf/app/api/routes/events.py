"""
Database API routes for retrieving stored OCSF events.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db, is_db_available
from app.database.repository import get_events, get_event_by_id

router = APIRouter(prefix="/events", tags=["events"])

def db_dependency():
    if not is_db_available():
        raise HTTPException(
            status_code=503,
            detail="Database is not configured or unavailable."
        )
    yield next(get_db())

@router.get("", response_model=List[Dict[str, Any]])
def list_events(limit: int = 50, offset: int = 0, db: Session = Depends(db_dependency)):
    """Retrieve paginated list of persisted OCSF events."""
    records = get_events(db, limit=limit, offset=offset)
    return [
        {
            "event_id": r.event_id,
            "timestamp": r.timestamp,
            "detected_format": r.detected_format,
            "parser": r.parser,
            "source_ip": r.source_ip,
            "destination_ip": r.destination_ip,
            "ocsf": r.ocsf,
            "created_at": r.created_at,
        }
        for r in records
    ]

@router.get("/{event_id}", response_model=Dict[str, Any])
def get_event(event_id: str, db: Session = Depends(db_dependency)):
    """Retrieve a single persisted OCSF event and its processing history by event_id."""
    record = get_event_by_id(db, event_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found.")
    
    history_data = None
    if record.history:
        history_data = {
            "validation_status": record.history.validation_status,
            "ocsf_validation_status": record.history.ocsf_validation_status,
            "mapping_source": record.history.mapping_source,
            "confidence": record.history.confidence,
            "ai_used": record.history.ai_used,
            "ai_status": record.history.ai_status,
            "validation_detail": record.history.validation_detail,
            "ocsf_validation_detail": record.history.ocsf_validation_detail,
            "provenance": record.history.provenance,
            "created_at": record.history.created_at,
        }

    return {
        "event_id": record.event_id,
        "timestamp": record.timestamp,
        "detected_format": record.detected_format,
        "parser": record.parser,
        "raw_event": record.raw_event,
        "source_ip": record.source_ip,
        "source_port": record.source_port,
        "destination_ip": record.destination_ip,
        "destination_port": record.destination_port,
        "ocsf": record.ocsf,
        "unmapped_fields": record.unmapped_fields,
        "history": history_data,
        "created_at": record.created_at,
    }
