from pydantic import BaseModel, Field
import uuid
from typing import Dict, Any, Optional, List
from app.models.universal_event import UniversalEvent

class ProcessingResult(BaseModel):
    """Common processing output contract for all modules."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_event: str
    source_file: Optional[str] = None
    source_file_index: Optional[int] = None
    detected_format: str
    parser: Optional[str] = None
    normalized_event: UniversalEvent
    unmapped_fields: Dict[str, Any]
    validation: Dict[str, Any]
    confidence: Dict[str, Any]
    provenance: Dict[str, Any]

class BatchProcessingResult(BaseModel):
    total: int
    processed: int
    results: List[ProcessingResult]
