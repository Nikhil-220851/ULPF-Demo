import traceback
from typing import Dict, Any

from app.models.input_event import InputEvent
from app.models.processing_result import ProcessingResult
from app.models.universal_event import UniversalEvent

from app.known_logs.detector import detect_format
from app.known_logs.normalizer import normalize_event
from app.unknown_logs.structure_analyzer import analyze_structure
from app.unknown_logs.semantic_mapper import map_semantics
from app.unknown_logs.confidence import calculate_confidence

from app.trust.validator import validate_event
from app.trust.provenance import track_provenance
from app.trust.quarantine import handle_error


def process_event(event: InputEvent) -> ProcessingResult:
    raw_payload = event.raw_payload
    
    try:
        # 1. Format Detection
        format_info = detect_format(raw_payload)
        detected_format = format_info.get("format", "UNKNOWN")
        
        parsed_data = {}
        unmapped_fields = {}
        confidence = {}
        provenance = {}
        
        parser_name = None
        if detected_format != "UNKNOWN":
            # 2a. Known Format Processing
            parser = format_info.get("parser")
            if parser:
                parser_name = format_info.get("parser_name", parser.__name__)
                parsed_data = parser(raw_payload)
            
            # 3a. Normalization
            normalized_event, unmapped_fields = normalize_event(parsed_data)
            
            confidence = {
                "overall": 0.98,
                "format": 1.0,
                "mapping": 0.98,
                "human_review_required": False
            }
        else:
            parser_name = "Adaptive Intelligence"
            # 2b. Unknown Log Processing
            structure = analyze_structure(raw_payload)
            
            # 3b. Semantic Mapping
            mapping_result = map_semantics(structure)
            normalized_event = mapping_result.get("normalized_event", UniversalEvent())
            unmapped_fields = mapping_result.get("unmapped_fields", {})
            confidence = mapping_result.get("confidence", {
                "overall": 0.0,
                "format": 0.0,
                "mapping": 0.0,
                "human_review_required": True
            })
            parsed_data = structure.get("tokens", {})
            
        # 4. Provenance / Traceability
        provenance = track_provenance(parsed_data, normalized_event)
        
        # 5. Validation
        validation_result = validate_event(normalized_event)
        
        return ProcessingResult(
            raw_event=raw_payload,
            source_file=event.source_file,
            source_file_index=event.source_file_index,
            detected_format=detected_format,
            parser=parser_name,
            normalized_event=normalized_event,
            unmapped_fields=unmapped_fields,
            validation=validation_result,
            confidence=confidence,
            provenance=provenance
        )
        
    except Exception as e:
        err_res = handle_error(raw_payload, str(e), traceback.format_exc())
        err_res.source_file = event.source_file
        err_res.source_file_index = event.source_file_index
        return err_res
