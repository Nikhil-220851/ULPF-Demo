"""
Repository layer providing data access methods for ULPF database entity persistence.
"""
import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.processing_result import ProcessingResult
from app.database.models import EventModel, ProcessingHistoryModel

logger = logging.getLogger(__name__)

def save_event(session: Session, result: ProcessingResult) -> EventModel:
    """
    Save a ProcessingResult's event data and history to PostgreSQL in a single transaction.
    """
    src_ip = None
    src_port = None
    dst_ip = None
    dst_port = None
    
    if result.ocsf:
        src = result.ocsf.get("src_endpoint", {})
        dst = result.ocsf.get("dst_endpoint", {})
        src_ip = src.get("ip")
        src_port = src.get("port")
        dst_ip = dst.get("ip")
        dst_port = dst.get("port")

    event_record = EventModel(
        event_id=result.event_id,
        detected_format=result.detected_format,
        parser=result.parser,
        raw_event=result.raw_event,
        source_ip=src_ip,
        source_port=src_port,
        destination_ip=dst_ip,
        destination_port=dst_port,
        ocsf=result.ocsf,
        unmapped_fields=result.unmapped_fields,
    )

    overall_conf = None
    if isinstance(result.confidence, dict):
        overall_conf = result.confidence.get("overall")

    mapping_src = "rule"
    if result.ai_used:
        mapping_src = "ai"
    elif result.detected_format == "CUSTOM_PLUGIN":
        mapping_src = "plugin"

    history_record = ProcessingHistoryModel(
        event_id=result.event_id,
        validation_status=result.validation.get("status", "UNKNOWN") if isinstance(result.validation, dict) else "UNKNOWN",
        ocsf_validation_status=result.ocsf_validation.get("status") if isinstance(result.ocsf_validation, dict) else None,
        mapping_source=mapping_src,
        confidence=overall_conf,
        ai_used=result.ai_used,
        ai_status=result.ai_status,
        validation_detail=result.validation if isinstance(result.validation, dict) else None,
        ocsf_validation_detail=result.ocsf_validation if isinstance(result.ocsf_validation, dict) else None,
        provenance=result.provenance if isinstance(result.provenance, dict) else None,
    )

    try:
        session.add(event_record)
        session.add(history_record)
        session.commit()
        session.refresh(event_record)
        return event_record
    except Exception as e:
        session.rollback()
        logger.error("Failed to save event to database: %s", e)
        raise e

def save_processing_history(session: Session, history_record: ProcessingHistoryModel) -> ProcessingHistoryModel:
    """Save processing history record independently."""
    try:
        session.add(history_record)
        session.commit()
        session.refresh(history_record)
        return history_record
    except Exception as e:
        session.rollback()
        logger.error("Failed to save processing history: %s", e)
        raise e

def get_event_by_id(session: Session, event_id: str) -> Optional[EventModel]:
    """Retrieve an event record by event_id."""
    stmt = select(EventModel).where(EventModel.event_id == event_id)
    return session.scalar(stmt)

def get_events(session: Session, limit: int = 50, offset: int = 0) -> List[EventModel]:
    """Retrieve a paginated list of event records."""
    stmt = select(EventModel).order_by(EventModel.id.desc()).offset(offset).limit(limit)
    return list(session.scalars(stmt).all())
