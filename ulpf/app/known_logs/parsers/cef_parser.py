import re

def parse(raw_payload: str) -> dict:
    parsed = {}
    
    # CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|[Extension]
    parts = raw_payload.split('|')
    if len(parts) >= 8:
        parsed['cef_version'] = parts[0].replace('CEF:', '')
        parsed['device_vendor'] = parts[1]
        parsed['device_product'] = parts[2]
        parsed['device_version'] = parts[3]
        parsed['signature_id'] = parts[4]
        parsed['name'] = parts[5]
        parsed['severity'] = parts[6]
        
        extension = '|'.join(parts[7:])
        
        # Parse extension key=value
        kv_pairs = re.findall(r'(\w+)=([^=]+)(?=\s+\w+=|$)', extension)
        for k, v in kv_pairs:
            parsed[k] = v.strip()
            
    return parsed
