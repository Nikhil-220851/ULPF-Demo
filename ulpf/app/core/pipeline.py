import traceback
from typing import Dict, Any, Optional

from app.models.input_event import InputEvent
from app.models.processing_result import ProcessingResult
from app.models.universal_event import UniversalEvent

from app.known_logs.detector import detect_format
from app.core.normalizer import normalize_event
from app.unknown_logs.structure_analyzer import analyze_structure
from app.unknown_logs.semantic_mapper import map_semantics
from app.unknown_logs.confidence import calculate_confidence

from app.trust.validator import validate_event
from app.trust.provenance import track_provenance
from app.trust.quarantine import handle_error

from app.config import AI_MAPPING_ENABLED, AI_MAPPING_THRESHOLD, DB_ENABLED
from app.services.ai.groq_provider import groq_provider
from app.services.ai.merger import merge_mappings
from app.services.ai.groq_provider import VALID_TARGET_FIELDS
from app.core.ocsf.mapper import map_to_ocsf
from app.core.ocsf.validator import validate_ocsf


def process_event(event: InputEvent, db: Any = None, ai_cache: Optional[Dict[str, Any]] = None) -> ProcessingResult:
    raw_payload = event.raw_payload
    
    try:
        # 1. Format Detection
        format_info = detect_format(raw_payload)
        detected_format = format_info.get("format", "UNKNOWN")
        
        parsed_data = {}
        unmapped_fields = {}
        confidence = {}
        provenance = {}
        structure = None
        mapping_result = {}
        ai_used = False
        ai_status = "not_applicable"
        
        parser_name = None
        if detected_format != "UNKNOWN":
            # 2a. Known Format Processing (CEF, Syslog, LEEF, JSON, CSV, or Stored Custom Plugins)
            parser = format_info.get("parser")
            if parser:
                parser_name = format_info.get("parser_name", parser.__name__ if hasattr(parser, '__name__') else "PluginParser")
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
            
            # 3b. Local Semantic Mapping
            mapping_result = map_semantics(structure)
            normalized_event = mapping_result.get("normalized_event", UniversalEvent())
            unmapped_fields = mapping_result.get("unmapped_fields", {})
            local_confidence = mapping_result.get("confidence", {})
            confidence = local_confidence
            parsed_data = structure.get("tokens", {})

            local_candidates = mapping_result.get("candidate_mappings", {})
            overall_local = local_confidence.get("overall", 0.0)

            # 3c. AI-Assisted Mapping for UNKNOWN events
            if AI_MAPPING_ENABLED:
                sig_key = f"{structure.get('format_type')}_{structure.get('delimiter')}_{structure.get('fields')}"
                ai_response = None
                if ai_cache is not None and sig_key in ai_cache:
                    ai_response = ai_cache[sig_key]
                else:
                    ai_response = groq_provider.suggest_mappings(
                        raw_log=raw_payload,
                        structure=structure,
                        candidate_mappings=local_candidates,
                        universal_schema=sorted(VALID_TARGET_FIELDS),
                    )
                    if ai_cache is not None and ai_response is not None:
                        ai_cache[sig_key] = ai_response

                if ai_response is not None:
                    merged = merge_mappings(local_candidates, ai_response)
                    mapping_result["candidate_mappings"] = merged
                    ai_used = True
                    ai_status = "success"
                    if isinstance(structure, dict):
                        structure["structure_source"] = "groq"
                        if ai_response.delimiter:
                            structure["delimiter"] = ai_response.delimiter

                    # Re-normalize using AI proposed mappings
                    parsed_ai_data = {}
                    tokens = structure.get("tokens", {})
                    for f_name, info in merged.items():
                        t_field = info.get("mapped_to")
                        val = info.get("value") or tokens.get(f_name)
                        if t_field and val is not None:
                            parsed_ai_data[t_field] = val

                    if parsed_ai_data:
                        normalized_event, unmapped_fields = normalize_event(parsed_ai_data)

                    merged_scores = [
                        v["confidence"] for v in merged.values() if v.get("mapped_to")
                    ]
                    if merged_scores:
                        avg = sum(merged_scores) / len(merged_scores)
                        confidence = {**confidence, "overall": avg, "mapping": avg}
                else:
                    ai_used = False
                    ai_status = "unavailable"
                    if isinstance(structure, dict):
                        structure["structure_source"] = "regex"
            elif AI_MAPPING_ENABLED and overall_local >= AI_MAPPING_THRESHOLD:
                ai_status = "skipped"   # local confidence was good enough
                if isinstance(structure, dict):
                    structure["structure_source"] = "regex"
            else:
                ai_status = "not_applicable"   # AI disabled in config
                if isinstance(structure, dict):
                    structure["structure_source"] = "regex"

        # 4. Provenance / Traceability
        provenance = track_provenance(parsed_data, normalized_event)
        
        # 5. Validation
        validation_result = validate_event(normalized_event)
        
        # Only populate structure and candidate_mappings for UNKNOWN events
        event_structure = structure if detected_format == "UNKNOWN" else None
        event_candidate_mappings = mapping_result.get("candidate_mappings") if detected_format == "UNKNOWN" else None
        
        # 6. OCSF Mapping and Validation
        ocsf_event, final_unmapped_fields = map_to_ocsf(normalized_event, unmapped_fields)
        ocsf_validation_result = validate_ocsf(ocsf_event)

        result = ProcessingResult(
            raw_event=raw_payload,
            source_file=event.source_file,
            source_file_index=event.source_file_index,
            detected_format=detected_format,
            parser=parser_name,
            normalized_event=normalized_event,
            unmapped_fields=final_unmapped_fields,
            validation=validation_result,
            confidence=confidence,
            provenance=provenance,
            structure=event_structure,
            candidate_mappings=event_candidate_mappings,
            ai_used=ai_used,
            ai_status=ai_status,
            ocsf=ocsf_event,
            ocsf_validation=ocsf_validation_result
        )

        # 7. Database Persistence
        if db is not None or DB_ENABLED:
            if db is not None:
                from app.database.repository import save_event
                save_event(db, result)
            else:
                from app.database.connection import is_db_available, get_engine
                if is_db_available():
                    from sqlalchemy.orm import Session
                    engine = get_engine()
                    if engine:
                        with Session(engine) as session:
                            from app.database.repository import save_event
                            save_event(session, result)

        return result
        
    except Exception as e:
        err_res = handle_error(raw_payload, str(e), traceback.format_exc())
        err_res.source_file = event.source_file
        err_res.source_file_index = event.source_file_index
        return err_res
