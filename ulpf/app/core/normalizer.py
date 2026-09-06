from typing import Dict, Any, Tuple, Optional
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
    "source.endpoint": ("source", "ip"),

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
    "destination.endpoint": ("destination", "ip"),

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
    "duser": ("user", "name"),

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

    # Bytes / Network Size
    "bytes": ("network", "bytes"),
    "byte_count": ("network", "bytes"),
    "bytecount": ("network", "bytes"),
    "bytes_sent": ("network", "bytes_sent"),
    "bytessent": ("network", "bytes_sent"),
    "bytes_received": ("network", "bytes_received"),
    "bytesreceived": ("network", "bytes_received")
}

UNIVERSAL_CATEGORIES = {"event", "source", "destination", "network", "user", "device"}

IPV4_REGEX = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")

def _is_ip(val: str) -> bool:
    return bool(isinstance(val, str) and IPV4_REGEX.match(val.strip()))

def _parse_composite_endpoint(val: Any) -> Tuple[Optional[str], Optional[int]]:
    """Extract (ip, port) from composite values.

    Handles:
      - [192.168.1.1:55120]  (square brackets, colon separator)
      - [192.168.1.1#55120]  (square brackets, hash separator)
      - 192.168.1.1:55120    (plain, colon separator)
      - 192.168.1.1#55120    (plain, hash separator)
    Returns (ip_str, port_int) or (ip_str, None) or (None, None).
    """
    if not isinstance(val, str):
        return None, None
    s = val.strip()
    # Strip surrounding square brackets, e.g. [192.168.1.1:55120]
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    delimiter = "#" if "#" in s else (":" if ":" in s else None)
    if delimiter:
        parts = s.split(delimiter, 1)
        if len(parts) == 2 and _is_ip(parts[0].strip()) and parts[1].strip().isdigit():
            port = int(parts[1].strip())
            if 1 <= port <= 65535:
                return parts[0].strip(), port
    if _is_ip(s):
        return s, None
    return None, None

def try_convert_port(value: Any) -> Any:
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def normalize_protocol(value: Any) -> Any:
    if isinstance(value, str):
        return value.lower()
    return value

def try_convert_timestamp(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    
    formats_to_try = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%b %d %H:%M:%S"
    ]
    
    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            if fmt == "%b %d %H:%M:%S":
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.isoformat()
        except ValueError:
            continue
            
    return value

def normalize_event(parsed_data: Dict[str, Any]) -> Tuple[UniversalEvent, Dict[str, Any]]:
    """
    Normalizes parsed log fields into the ULPF UniversalEvent schema.
    Supports composite values (IP#PORT) and composite date/time tokens.
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

    populated_paths = set()

    def set_field(category: str, subfield: str, val: Any, orig_key: str):
        path = f"{category}.{subfield}" if subfield else category
        if path in populated_paths:
            unmapped_fields[orig_key] = val
            return

        # Check composite IP#PORT, IP:PORT, or [IP:PORT] / [IP#PORT]
        # Trigger on any source/destination field if the value looks like a compound endpoint
        _looks_composite = (
            isinstance(val, str) and (
                (val.strip().startswith("[") and val.strip().endswith("]"))
                or "#" in val
                or (":" in val and any(c.isdigit() for c in val.split(":", 1)[-1][:6]))
            )
        )
        if category in ("source", "destination") and (
            subfield in ("ip", "endpoint", "port") or _looks_composite
        ):
            ip_part, port_part = _parse_composite_endpoint(val)
            if ip_part:
                normalized_data[category]["ip"] = ip_part
                populated_paths.add(f"{category}.ip")
                if port_part is not None:
                    normalized_data[category]["port"] = port_part
                    populated_paths.add(f"{category}.port")
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
                unmapped_fields[orig_key] = val
        else:
            unmapped_fields[orig_key] = val
        populated_paths.add(path)

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
            unmapped_fields[key] = value

    # Composite Timestamp Pairing Check:
    # If date and time exist in separate tokens, combine them into event.timestamp
    if "timestamp" not in normalized_data["event"]:
        date_val = None
        time_val = None
        for k, v in list(unmapped_fields.items()):
            if isinstance(v, str):
                v_strip = v.strip()
                if not date_val and re.match(r"^\d{4}[-/]\d{2}[-/]\d{2}$", v_strip):
                    date_val = v_strip
                elif not time_val and re.match(r"^\d{2}:\d{2}:\d{2}(?:\.\d+)?$", v_strip):
                    time_val = v_strip
        if date_val:
            combined_ts = f"{date_val} {time_val}" if time_val else date_val
            normalized_data["event"]["timestamp"] = try_convert_timestamp(combined_ts)

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
