from typing import Dict, Any, Tuple
from app.models.universal_event import UniversalEvent

FIELD_MAPPINGS = {
    "source_ip": ("source", "ip"),
    "src": ("source", "ip"),
    "srcip": ("source", "ip"),
    "destination_ip": ("destination", "ip"),
    "dst": ("destination", "ip"),
    "dstip": ("destination", "ip"),
    "source_port": ("source", "port"),
    "sport": ("source", "port"),
    "spt": ("source", "port"),
    "destination_port": ("destination", "port"),
    "dport": ("destination", "port"),
    "dpt": ("destination", "port"),
    "action": ("event", "action"),
    "act": ("event", "action"),
    "hostname": ("device", "hostname"),
    "protocol": ("network", "protocol"),
    "severity": ("severity", None)
}

def normalize_event(parsed_data: Dict[str, Any]) -> Tuple[UniversalEvent, Dict[str, Any]]:
    normalized_data = {
        "event": {},
        "source": {},
        "destination": {},
        "network": {},
        "user": {},
        "device": {}
    }
    severity = None
    unmapped_fields = {}
    
    for key, value in parsed_data.items():
        lower_key = key.lower()
        if lower_key in FIELD_MAPPINGS:
            category, subfield = FIELD_MAPPINGS[lower_key]
            if category == "severity":
                severity = str(value)
            else:
                normalized_data[category][subfield] = value
        elif "." in lower_key:
            category, subfield = lower_key.split(".", 1)
            if category in normalized_data:
                normalized_data[category][subfield] = value
            else:
                unmapped_fields[key] = value
        else:
            unmapped_fields[key] = value
            
    event = UniversalEvent(
        event=normalized_data["event"],
        source=normalized_data["source"],
        destination=normalized_data["destination"],
        network=normalized_data["network"],
        user=normalized_data["user"],
        device=normalized_data["device"],
        severity=severity
    )
    return event, unmapped_fields
