from app.unknown_logs.structure_analyzer import analyze_structure

def parse_with_plugin(raw_payload: str, plugin_def: dict) -> dict:
    sig = plugin_def.get("signature", {})
    format_type = sig.get("format_type", "delimited")
    
    parsed = {}
    mappings = plugin_def.get("field_mappings", {})
    
    # Use structure analyzer to parse the raw payload accurately
    structure = analyze_structure(raw_payload)
    tokens = structure.get("tokens", {})
    
    if format_type == "delimited":
        # For simple delimited logs, tokens might be named "field_1", "field_2"
        # We also need to support old plugins which mapped by integer indices "0", "1"
        for map_key, mapped_to in mappings.items():
            if map_key in tokens:
                parsed[mapped_to] = tokens[map_key]
            else:
                try:
                    idx = int(map_key)
                    # "0" -> "field_1"
                    field_key = f"field_{idx + 1}"
                    if field_key in tokens:
                        parsed[mapped_to] = tokens[field_key]
                except ValueError:
                    pass
    else:
        # For multiline_bracketed and others, use the exact token keys (e.g., "FROM_IP")
        for map_key, mapped_to in mappings.items():
            if map_key in tokens:
                parsed[mapped_to] = tokens[map_key]
            
    return parsed
