from typing import Dict, Any, Tuple
from datetime import datetime
import re
from app.models.universal_event import UniversalEvent

# Comprehensive mapping of common source log fields to ULPF Universal Schema
FIELD_MAPPINGS = {
    # Source IP
    "src": ("source", "ip"),
    "src_ip": ("source", "ip"),
    "srcip": ("source", "ip"),
    "source": ("source", "ip"),
    "source_ip": ("source", "ip"),
    "sourceip": ("source", "ip"),
    "source_address": ("source", "ip"),
    "sourceaddress": ("source", "ip"),
    "client_ip": ("source", "ip"),
    "clientip": ("source", "ip"),
    "client_address": ("source", "ip"),
    "clientaddress": ("source", "ip"),
    "origin_ip": ("source", "ip"),
    "originip": ("source", "ip"),

    # Destination IP
    "dst": ("destination", "ip"),
    "dst_ip": ("destination", "ip"),
    "dstip": ("destination", "ip"),
    "destination": ("destination", "ip"),
    "destination_ip": ("destination", "ip"),
    "destinationip": ("destination", "ip"),
    "destination_address": ("destination", "ip"),
    "destinationaddress": ("destination", "ip"),
    "dest_ip": ("destination", "ip"),
    "destip": ("destination", "ip"),
    "server_ip": ("destination", "ip"),
    "serverip": ("destination", "ip"),

    # Source Port
    "src_port": ("source", "port"),
    "srcport": ("source", "port"),
    "source_port": ("source", "port"),
    "sourceport": ("source", "port"),
    "client_port": ("source", "port"),
    "clientport": ("source", "port"),
    "spt": ("source", "port"),
    "sport": ("source", "port"),

    # Destination Port
    "dst_port": ("destination", "port"),
    "dstport": ("destination", "port"),
    "destination_port": ("destination", "port"),
    "destinationport": ("destination", "port"),
    "dest_port": ("destination", "port"),
    "destport": ("destination", "port"),
    "server_port": ("destination", "port"),
    "serverport": ("destination", "port"),
    "dpt": ("destination", "port"),
    "dport": ("destination", "port"),

    # Network Protocol
    "proto": ("network", "transport"),
    "protocol": ("network", "transport"),
    "transport": ("network", "transport"),
    "transport_protocol": ("network", "transport"),
    "network_protocol": ("network", "transport"),

    # User
    "user": ("user", "name"),
    "username": ("user", "name"),
    "user_name": ("user", "name"),
    "userid": ("user", "name"),
    "user_id": ("user", "name"),
    "account": ("user", "name"),
    "account_name": ("user", "name"),
    "login": ("user", "name"),
    "login_user": ("user", "name"),
    "duser": ("user", "name"), # CEF destination user

    # Message / Description
    "msg": ("event", "message"),
    "message": ("event", "message"),
    "event_message": ("event", "message"),
    "eventmessage": ("event", "message"),
    "description": ("event", "message"),
    "desc": ("event", "message"),
    "details": ("event", "message"),
    "reason": ("event", "message"),

    # Application / Service
    "app": ("event", "application"),
    "application": ("event", "application"),
    "application_name": ("event", "application"),
    "applicationname": ("event", "application"),
    "service": ("event", "service"),
    "service_name": ("event", "service"),
    "servicename": ("event", "service"),
    "program": ("event", "service"),

    # Process
    "pid": ("event", "process_id"),
    "process_id": ("event", "process_id"),
    "processid": ("event", "process_id"),
    "process_name": ("event", "process_name"),
    "processname": ("event", "process_name"),
    "process": ("event", "process_name"),
    "command": ("event", "command"),
    "command_line": ("event", "command"),
    "cmdline": ("event", "command"),

    # Event Identifiers
    "event_id": ("event", "id"),
    "eventid": ("event", "id"),
    "event_code": ("event", "id"),
    "eventcode": ("event", "id"),
    "code": ("event", "id"),
    "signature_id": ("event", "id"),
    "signatureid": ("event", "id"),
    "event_type": ("event", "type"),
    "eventtype": ("event", "type"),
    "type": ("event", "type"),
    "event_category": ("event", "category"),
    "category": ("event", "category"),
    "eventcategory": ("event", "category"),
    
    # CEF specific actions
    "act": ("event", "action"),
    "action": ("event", "action"),

    # Timestamp
    "timestamp": ("event", "timestamp"),
    "time": ("event", "timestamp"),
    "ts": ("event", "timestamp"),
    "datetime": ("event", "timestamp"),
    "date_time": ("event", "timestamp"),
    "event_time": ("event", "timestamp"),
    "eventtime": ("event", "timestamp"),
    "created_at": ("event", "timestamp"),
    "createdat": ("event", "timestamp"),
    "logged_at": ("event", "timestamp"),
    "loggedat": ("event", "timestamp"),

    # URL / Host / Path
    "url": ("event", "url"),
    "uri": ("event", "url"),
    "request_url": ("event", "url"),
    "request_uri": ("event", "url"),
    "http_url": ("event", "url"),
    "host": ("device", "hostname"),
    "hostname": ("device", "hostname"),
    "host_name": ("device", "hostname"),
    "device": ("device", "hostname"),
    "device_name": ("device", "hostname"),
    "devicename": ("device", "hostname"),
    "path": ("event", "path"),
    "file": ("event", "path"),
    "file_path": ("event", "path"),
    "filepath": ("event", "path"),

    # Country / Location
    "country": ("source", "country"),
    "country_code": ("source", "country"),
    "countrycode": ("source", "country"),
    "geo_country": ("source", "country"),
    "geocountry": ("source", "country"),

    # Bytes / Network Size
    "bytes": ("network", "bytes"),
    "byte_count": ("network", "bytes"),
    "bytecount": ("network", "bytes"),
    "bytes_sent": ("network", "bytes_sent"),
    "bytessent": ("network", "bytes_sent"),
    "bytes_received": ("network", "bytes_received"),
    "bytesreceived": ("network", "bytes_received")
}

# The universal schema categories we support dynamically constructing
UNIVERSAL_CATEGORIES = {"event", "source", "destination", "network", "user", "device"}

def try_convert_port(value: Any) -> Any:
    """Attempts to convert port to integer safely. Returns original value if it fails."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def normalize_protocol(value: Any) -> Any:
    """Normalizes protocol strings (e.g. TCP -> tcp)."""
    if isinstance(value, str):
        return value.lower()
    return value

def try_convert_timestamp(value: Any) -> Any:
    """Attempts to convert common timestamp formats to ISO-8601. Returns original on failure."""
    if not isinstance(value, str):
        return value
    
    # Very basic parsing attempts for common formats
    formats_to_try = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%b %d %H:%M:%S" # Syslog format
    ]
    
    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            # If syslog format, inject current year
            if fmt == "%b %d %H:%M:%S":
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.isoformat()
        except ValueError:
            continue
            
    return value

def normalize_event(parsed_data: Dict[str, Any]) -> Tuple[UniversalEvent, Dict[str, Any]]:
    """
    Normalizes parsed log fields into the ULPF UniversalEvent schema.
    Returns a tuple of (normalized_event, unmapped_fields)
    """
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

    # Track fields we've already set to avoid overwriting with lower-priority aliases
    # We track by f"{category}.{subfield}"
    populated_paths = set()

    def set_field(category: str, subfield: str, val: Any, orig_key: str):
        path = f"{category}.{subfield}" if subfield else category
        if path in populated_paths:
            # Deterministic conflict handling: Push conflicting duplicate to unmapped
            unmapped_fields[orig_key] = val
            return

        # Type Conversions
        if category in ("source", "destination") and subfield == "port":
            val = try_convert_port(val)
        elif category == "network" and subfield == "transport":
            val = normalize_protocol(val)
        elif category == "event" and subfield == "timestamp":
            val = try_convert_timestamp(val)

        if category == "severity":
            nonlocal severity
            severity = str(val)
        elif category in normalized_data:
            if subfield is not None:
                normalized_data[category][subfield] = val
            else:
                unmapped_fields[orig_key] = val # should not happen via mappings
        else:
            unmapped_fields[orig_key] = val
        populated_paths.add(path)

    # We do a two-pass mapping to ensure plugin/exact matches take priority
    
    # Pass 1: Exact matches (like "source.ip" provided by plugin or unknown-log mapper)
    remaining_fields = {}
    for key, value in parsed_data.items():
        if "." in key:
            cat, sub = key.split(".", 1)
            if cat in UNIVERSAL_CATEGORIES:
                set_field(cat, sub, value, orig_key=key)
            else:
                remaining_fields[key] = value
        else:
            remaining_fields[key] = value

    # Pass 2: Alias matching using FIELD_MAPPINGS
    for key, value in remaining_fields.items():
        lower_key = key.lower()
        if lower_key in FIELD_MAPPINGS:
            cat, sub = FIELD_MAPPINGS[lower_key]
            set_field(cat, sub, value, orig_key=key)
        else:
            # Unmapped
            unmapped_fields[key] = value

    event = UniversalEvent(
        event=normalized_data.get("event"),
        source=normalized_data.get("source"),
        destination=normalized_data.get("destination"),
        network=normalized_data.get("network"),
        user=normalized_data.get("user"),
        device=normalized_data.get("device"),
        severity=severity
    )
    return event, unmapped_fields
