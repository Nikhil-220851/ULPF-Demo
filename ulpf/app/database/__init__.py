"""
Database package for ULPF.
"""
from app.database.connection import get_db, init_db, is_db_available
from app.database.models import EventModel, ProcessingHistoryModel
from app.database.repository import (
    save_event,
    get_event_by_id,
    get_events,
    save_processing_history,
)

__all__ = [
    "get_db",
    "init_db",
    "is_db_available",
    "EventModel",
    "ProcessingHistoryModel",
    "save_event",
    "get_event_by_id",
    "get_events",
    "save_processing_history",
]
