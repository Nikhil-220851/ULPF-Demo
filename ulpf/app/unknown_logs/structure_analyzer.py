import re

def analyze_structure(raw_payload: str) -> dict:
    structure = {
        "delimiter": None,
        "fields": 0,
        "data_types": [],
        "tokens": {}
    }
    
    # Try finding common delimiters: |, \t, ;
    for delim in ['|', '\t', ';']:
        if delim in raw_payload:
            structure["delimiter"] = delim
            break
            
    if not structure["delimiter"]:
        structure["delimiter"] = " " # fallback to space
        
    parts = [p.strip() for p in raw_payload.split(structure["delimiter"]) if p.strip()]
    structure["fields"] = len(parts)
    
    for i, part in enumerate(parts):
        token_type = "UNKNOWN"
        # Check IP
        if re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', part):
            token_type = "IP"
        # Check Port
        elif re.match(r'^\d+$', part) and 1 <= int(part) <= 65535:
            token_type = "PORT"
        # Check Action
        elif part.upper() in ["ALLOW", "DENY", "DROP", "REJECT", "ACCEPT", "BLOCK"]:
            token_type = "ACTION"
            
        structure["data_types"].append(token_type)
        structure["tokens"][f"field_{i+1}"] = part
        
    return structure
