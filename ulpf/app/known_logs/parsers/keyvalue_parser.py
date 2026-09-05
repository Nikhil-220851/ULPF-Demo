import re

def parse(raw_payload: str) -> dict:
    parsed = {}
    
    kv_pairs = re.findall(r'(\w+)=([^=\s]+)', raw_payload)
    for k, v in kv_pairs:
        parsed[k.lower()] = v.strip()
        
    return parsed
