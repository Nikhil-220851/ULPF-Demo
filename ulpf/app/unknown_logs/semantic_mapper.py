from app.models.universal_event import UniversalEvent

def map_semantics(structure: dict) -> dict:
    normalized_event = UniversalEvent()
    unmapped_fields = {}
    candidate_mappings = {}
    
    data_types = structure.get("data_types", [])
    tokens = structure.get("tokens", {})
    
    ip_count = 0
    port_count = 0
    
    for i, (field_name, value) in enumerate(tokens.items()):
        token_type = data_types[i] if i < len(data_types) else "UNKNOWN"
        confidence_score = 0.0
        mapped_to = None
        
        if token_type == "IP":
            if ip_count == 0:
                mapped_to = "source.ip"
                confidence_score = 0.90 # Candidate mapping, high but not 1.0
                normalized_event.source["ip"] = value
            elif ip_count == 1:
                mapped_to = "destination.ip"
                confidence_score = 0.88
                normalized_event.destination["ip"] = value
            else:
                unmapped_fields[field_name] = value
                
            ip_count += 1
            
        elif token_type == "PORT":
            if port_count == 0:
                mapped_to = "source.port"
                confidence_score = 0.85
                normalized_event.source["port"] = value
            elif port_count == 1:
                mapped_to = "destination.port"
                confidence_score = 0.83
                normalized_event.destination["port"] = value
            else:
                unmapped_fields[field_name] = value
                
            port_count += 1
            
        elif token_type == "ACTION":
            mapped_to = "event.action"
            confidence_score = 0.95
            normalized_event.event["action"] = value
            
        else:
            unmapped_fields[field_name] = value
            
        candidate_mappings[field_name] = {
            "mapped_to": mapped_to,
            "confidence": confidence_score,
            "value": value
        }
    
    # Calculate overall confidence
    scores = [v["confidence"] for v in candidate_mappings.values() if v["mapped_to"] is not None]
    overall_confidence = sum(scores) / len(scores) if scores else 0.0
    
    human_review = overall_confidence < 0.90 or bool(unmapped_fields)
    
    return {
        "normalized_event": normalized_event,
        "unmapped_fields": unmapped_fields,
        "candidate_mappings": candidate_mappings,
        "confidence": {
            "overall": overall_confidence,
            "format": 0.5,
            "mapping": overall_confidence,
            "human_review_required": human_review
        }
    }
