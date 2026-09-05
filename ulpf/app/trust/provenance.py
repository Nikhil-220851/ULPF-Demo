from app.models.universal_event import UniversalEvent

def track_provenance(parsed_data: dict, normalized_event: UniversalEvent) -> dict:
    provenance = {}
    
    # We want: Universal field -> Original field -> Original value
    # Since we mapped lower_key -> universal field in normalizer, 
    # we need to reconstruct or approximate it.
    # For a robust implementation, normalizer should return the mapping trace.
    # Here we do a simplified reconstruction based on values.
    
    # Extract all universal fields with values
    univ_fields = {}
    for category, fields in normalized_event.model_dump().items():
        if isinstance(fields, dict):
            for k, v in fields.items():
                if v:
                    univ_fields[f"{category}.{k}"] = v
        elif fields:
            univ_fields[category] = fields
            
    for u_key, u_val in univ_fields.items():
        for p_key, p_val in parsed_data.items():
            # Simple match by value, in a real system we'd track the exact mapping
            if str(u_val) == str(p_val):
                provenance[u_key] = {
                    "original_field": p_key,
                    "original_value": p_val
                }
                break
                
    return provenance
