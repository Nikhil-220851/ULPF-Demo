from app.models.universal_event import UniversalEvent
import re

# Map bracket-label prefixes to universal fields (for multiline_bracketed formats)
_LABEL_MAP = {
    "FROM_IP": "source.ip",
    "FROM_PORT": "source.port",
    "TO_IP": "destination.ip",
    "TO_PORT": "destination.port",
    "USER": "user.name",
    "SERVICE": "event.application",
    "STATUS": "event.action",
    "ACTION": "event.action",
}


def _set_nested(event: UniversalEvent, universal_path: str, value):
    """Set a value on the UniversalEvent using a dotted path like 'source.ip'."""
    parts = universal_path.split(".", 1)
    category = parts[0]
    subfield = parts[1] if len(parts) > 1 else None
    if not subfield:
        return
    target = getattr(event, category, None)
    if isinstance(target, dict):
        # Safe port conversion
        if subfield == "port":
            try:
                value = int(value)
            except (ValueError, TypeError):
                pass
        target[subfield] = value


def map_semantics(structure: dict) -> dict:
    normalized_event = UniversalEvent()
    unmapped_fields = {}
    candidate_mappings = {}

    data_types = structure.get("data_types", [])
    tokens = structure.get("tokens", {})
    format_type = structure.get("format_type", "delimited")

    ip_count = 0
    port_count = 0
    ts_assigned = False
    hostname_assigned = False

    for i, (field_name, value) in enumerate(tokens.items()):
        token_type = data_types[i] if i < len(data_types) else "UNKNOWN"
        confidence_score = 0.0
        mapped_to = None

        # --- Label-based mapping (for multiline_bracketed formats) ---
        if format_type == "multiline_bracketed" and field_name in _LABEL_MAP:
            mapped_to = _LABEL_MAP[field_name]
            confidence_score = 0.95
            _set_nested(normalized_event, mapped_to, value)

        # --- Type-based positional mapping ---
        elif token_type in ("IP", "COMPOSITE_ENDPOINT"):
            if ip_count == 0:
                mapped_to = "source.ip"
                confidence_score = 0.94 if token_type == "COMPOSITE_ENDPOINT" else 0.90
                normalized_event.source["ip"] = value
            elif ip_count == 1:
                mapped_to = "destination.ip"
                confidence_score = 0.92 if token_type == "COMPOSITE_ENDPOINT" else 0.88
                normalized_event.destination["ip"] = value
            else:
                unmapped_fields[field_name] = value
            ip_count += 1

        elif token_type == "PORT":
            port_val = value
            try:
                port_val = int(value)
            except (ValueError, TypeError):
                pass
            if port_count == 0:
                mapped_to = "source.port"
                confidence_score = 0.85
                normalized_event.source["port"] = port_val
            elif port_count == 1:
                mapped_to = "destination.port"
                confidence_score = 0.83
                normalized_event.destination["port"] = port_val
            else:
                unmapped_fields[field_name] = value
            port_count += 1

        elif token_type == "PROTOCOL":
            mapped_to = "network.transport"
            confidence_score = 0.90
            normalized_event.network["transport"] = value

        elif token_type == "ACTION":
            mapped_to = "event.action"
            confidence_score = 0.92
            normalized_event.event["action"] = value

        elif token_type == "TIMESTAMP":
            if not ts_assigned:
                mapped_to = "event.timestamp"
                confidence_score = 0.90
                normalized_event.event["timestamp"] = value
                ts_assigned = True
            else:
                unmapped_fields[field_name] = value

        elif token_type == "MESSAGE":
            mapped_to = "event.message"
            confidence_score = 0.88
            normalized_event.event["message"] = value

        else:
            # Try to infer from field name label for non-bracket single-line formats
            fname_upper = field_name.upper()
            if not ts_assigned and fname_upper in ("TS", "TIME", "TIMESTAMP", "DATE"):
                mapped_to = "event.timestamp"
                confidence_score = 0.80
                normalized_event.event["timestamp"] = value
                ts_assigned = True
            elif not hostname_assigned and fname_upper in ("HOST", "HOSTNAME", "GW", "DEVICE"):
                mapped_to = "device.hostname"
                confidence_score = 0.78
                normalized_event.device["hostname"] = value
                hostname_assigned = True
            else:
                unmapped_fields[field_name] = value

        candidate_mappings[field_name] = {
            "mapped_to": mapped_to,
            "confidence": confidence_score,
            "value": value,
            "token_type": token_type,
        }

    # Hostname heuristic for unlabeled second fields in multiline that look like a hostname
    if format_type == "multiline_bracketed" and not hostname_assigned:
        for field_name, info in candidate_mappings.items():
            if info["mapped_to"] is None and info["token_type"] == "UNKNOWN":
                val = str(info["value"])
                # Simple hostname heuristic: short alphanumeric-with-dash, has letters
                if re.match(r'^[A-Za-z][A-Za-z0-9\-]+$', val):
                    candidate_mappings[field_name]["mapped_to"] = "device.hostname"
                    candidate_mappings[field_name]["confidence"] = 0.72
                    normalized_event.device["hostname"] = val
                    unmapped_fields.pop(field_name, None)
                    break

    # Calculate overall confidence
    scores = [v["confidence"] for v in candidate_mappings.values() if v["mapped_to"] is not None]
    overall_confidence = sum(scores) / len(scores) if scores else 0.0
    human_review = overall_confidence < 0.90 or bool(unmapped_fields)

    return {
        "normalized_event": normalized_event,
        "unmapped_fields": unmapped_fields,
        "candidate_mappings": candidate_mappings,
        "confidence": {
            "overall": overall_confidence,
            "format": 0.5,
            "mapping": overall_confidence,
            "human_review_required": human_review,
        },
    }
