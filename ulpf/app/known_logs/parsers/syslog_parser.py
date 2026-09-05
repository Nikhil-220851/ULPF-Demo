import re

def parse(raw_payload: str) -> dict:
    parsed = {}
    
    # Syslog example: Sep 04 10:32:15 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 SRCPORT=443 ACTION=ALLOW
    # Extract timestamp and hostname
    match = re.match(r'^([A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(.*)', raw_payload)
    if match:
        parsed['timestamp'] = match.group(1)
        parsed['hostname'] = match.group(2)
        remainder = match.group(3)
        
        kv_pairs = re.findall(r'(\w+)=([^=\s]+)', remainder)
        for k, v in kv_pairs:
            parsed[k.lower()] = v.strip()
    
    return parsed
