"""
Tests for PostgreSQL database integration using an isolated SQLite in-memory database
(simulating PostgreSQL ORM behavior via SQLAlchemy dialect abstraction).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.connection import Base
from app.database.models import EventModel, ProcessingHistoryModel
from app.database.repository import save_event, get_event_by_id, get_events
from app.models.input_event import InputEvent
from app.models.processing_result import ProcessingResult
from app.models.universal_event import UniversalEvent

@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_save_and_retrieve_event(db_session):
    result = ProcessingResult(
        event_id="test-event-uuid-123",
        raw_event="CEF:0|PaloAlto|Firewall|11.0|1001|Traffic|5|src=192.168.1.30 dst=10.0.0.10 spt=8080 dpt=443 proto=TCP act=ALLOW",
        detected_format="CEF",
        parser="cef_parser",
        normalized_event=UniversalEvent(),
        unmapped_fields={"custom_field": "val"},
        validation={"status": "VALID", "errors": []},
        confidence={"overall": 0.98},
        provenance={"timestamp": "2026-09-05T18:00:00Z"},
        ai_used=False,
        ai_status="not_applicable",
        ocsf={
            "metadata": {"version": "1.3.0"},
            "class_uid": 4001,
            "category_uid": 4,
            "src_endpoint": {"ip": "192.168.1.30", "port": 8080},
            "dst_endpoint": {"ip": "10.0.0.10", "port": 443},
            "activity_id": 1,
            "activity_name": "ALLOW"
        },
        ocsf_validation={"status": "VALID", "errors": []}
    )

    saved_event = save_event(db_session, result)
    assert saved_event.id is not None
    assert saved_event.event_id == "test-event-uuid-123"
    assert saved_event.source_ip == "192.168.1.30"
    assert saved_event.source_port == 8080
    assert saved_event.destination_ip == "10.0.0.10"
    assert saved_event.destination_port == 443
    assert saved_event.ocsf["class_uid"] == 4001

    retrieved = get_event_by_id(db_session, "test-event-uuid-123")
    assert retrieved is not None
    assert retrieved.detected_format == "CEF"
    assert retrieved.history is not None
    assert retrieved.history.validation_status == "VALID"
    assert retrieved.history.ocsf_validation_status == "VALID"
    assert retrieved.history.ai_used is False

def test_get_events_pagination(db_session):
    for i in range(5):
        res = ProcessingResult(
            event_id=f"event-{i}",
            raw_event=f"raw-{i}",
            detected_format="JSON",
            normalized_event=UniversalEvent(),
            unmapped_fields={},
            validation={"status": "VALID"},
            confidence={"overall": 1.0},
            provenance={},
            ocsf={"class_uid": 4001},
            ocsf_validation={"status": "VALID"}
        )
        save_event(db_session, res)

    events = get_events(db_session, limit=3, offset=0)
    assert len(events) == 3

def test_pipeline_with_db_session(db_session):
    from app.core.pipeline import process_event
    event = InputEvent(raw_payload='{"source_ip": "192.168.1.50", "destination_ip": "10.0.0.1", "source_port": 1234, "destination_port": 80}')
    
    result = process_event(event, db=db_session)
    assert result.event_id is not None

    record = get_event_by_id(db_session, result.event_id)
    assert record is not None
    assert record.source_ip == "192.168.1.50"
    assert record.destination_ip == "10.0.0.1"
    assert record.history.ocsf_validation_status == "VALID"

def test_pipeline_without_db():
    """
    Verify the core pipeline runs end-to-end when no database session is supplied
    and DB_ENABLED is effectively false (db=None).  No persistence is attempted;
    the ProcessingResult must still be fully populated.
    """
    from app.core.pipeline import process_event
    import app.core.pipeline as pl
    original = pl.DB_ENABLED
    try:
        # Simulate DB_ENABLED=false at runtime
        pl.DB_ENABLED = False
        event = InputEvent(raw_payload='{"source_ip": "10.1.1.1", "destination_ip": "10.2.2.2"}')
        result = process_event(event, db=None)
        assert result is not None
        assert result.raw_event == '{"source_ip": "10.1.1.1", "destination_ip": "10.2.2.2"}'
        assert result.detected_format is not None
        assert result.ocsf is not None
    finally:
        # Always restore the original flag so other tests are not affected
        pl.DB_ENABLED = original
