import re
from app.models.universal_event import UniversalEvent

def validate_event(event: UniversalEvent) -> dict:
    errors = []
    warnings = []
    
    # Validate IPs
    ip_pattern = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
    
    def is_valid_ip(ip_str):
        if not re.match(ip_pattern, ip_str): return False
        try:
            return all(0 <= int(octet) <= 255 for octet in ip_str.split('.'))
        except:
            return False

    if event.source.get('ip'):
        if not is_valid_ip(str(event.source['ip'])):
            errors.append({"field": "source.ip", "message": "Invalid IP address format"})
            
    if event.destination.get('ip'):
        if not is_valid_ip(str(event.destination['ip'])):
            errors.append({"field": "destination.ip", "message": "Invalid IP address format"})
            
    # Validate Ports
    if event.source.get('port'):
        try:
            port = int(event.source['port'])
            if not (1 <= port <= 65535):
                errors.append({"field": "source.port", "message": "Port out of range"})
        except ValueError:
            errors.append({"field": "source.port", "message": "Port must be an integer"})
            
    if event.destination.get('port'):
        try:
            port = int(event.destination['port'])
            if not (1 <= port <= 65535):
                errors.append({"field": "destination.port", "message": "Port out of range"})
        except ValueError:
            errors.append({"field": "destination.port", "message": "Port must be an integer"})
            
    if errors:
        return {"status": "INVALID", "errors": errors, "warnings": warnings}
        
    return {"status": "VALID", "errors": [], "warnings": warnings}
