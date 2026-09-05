def parse_with_plugin(raw_payload: str, plugin_def: dict) -> dict:
    sig = plugin_def.get("signature", {})
    delim = sig.get("delimiter", " ")
    parts = [p.strip() for p in raw_payload.split(delim) if p.strip()]
    
    parsed = {}
    mappings = plugin_def.get("field_mappings", {})
    
    for str_index, mapped_to in mappings.items():
        try:
            idx = int(str_index)
            if idx < len(parts):
                # mapped_to is like 'source.ip', we can keep it as is, normalizer will handle flattened dicts
                # wait, normalizer.py expects standard fields or nested dicts?
                # Actually, our normalizer can handle nested if we construct it, or simple dictionary.
                # Let's map it straight to the dict key
                # Wait, normalizer expects: "source_ip", "dest_ip" OR we can output the exact field paths
                # Let's just put it in the parsed dict and let normalization handle it
                parsed[mapped_to] = parts[idx]
        except ValueError:
            pass
            
    return parsed
