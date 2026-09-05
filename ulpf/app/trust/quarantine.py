from typing import Dict, Any
from app.models.processing_result import ProcessingResult
from app.models.universal_event import UniversalEvent

def handle_error(raw_payload: str, error_message: str, stack_trace: str) -> ProcessingResult:
    return ProcessingResult(
        raw_event=raw_payload,
        detected_format="UNKNOWN",
        normalized_event=UniversalEvent(),
        unmapped_fields={},
        validation={
            "status": "ERROR",
            "errors": [{"field": "system", "message": error_message}],
            "warnings": [],
            "stack_trace": stack_trace
        },
        confidence={
            "overall": 0.0,
            "format": 0.0,
            "mapping": 0.0,
            "human_review_required": True
        },
        provenance={}
    )
