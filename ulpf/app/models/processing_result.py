from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.models.universal_event import UniversalEvent

class ProcessingResult(BaseModel):
    """Common processing output contract for all modules."""
    raw_event: str
    detected_format: str
    normalized_event: UniversalEvent
    unmapped_fields: Dict[str, Any]
    validation: Dict[str, Any]
    confidence: Dict[str, Any]
    provenance: Dict[str, Any]
