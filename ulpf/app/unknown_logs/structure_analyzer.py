import re

# Regex for bracket-wrapped tokens like FROM[192.168.1.1#54321] or USER[admin]
_BRACKET_PATTERN = re.compile(r'^([A-Z_]+)\[(.+)\]$')
# IP address
_IP_PATTERN = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$')
# Timestamp-like values
_TIMESTAMP_PATTERN = re.compile(r'^\d{8}:\d{6}$')  # e.g. 20260905:143218
# Hostname: alphanumeric with dashes, has at least one letter, no spaces
_HOSTNAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*$')
# ALL_CAPS word — action/status/service indicator
_ACTION_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]{1,}$')
# Quoted string: "some message"
_QUOTED_PATTERN = re.compile(r'^"(.+)"$')


def _classify_token(value: str) -> str:
    """Classify a single token string into a semantic type."""
    v = value.strip()
    if _IP_PATTERN.match(v):
        return "IP"
    if re.match(r'^\d+$', v) and 1 <= int(v) <= 65535:
        return "PORT"
    if _TIMESTAMP_PATTERN.match(v):
        return "TIMESTAMP"
    if v.startswith('<') and v.endswith('>'):
        inner = v[1:-1]
        if _TIMESTAMP_PATTERN.match(inner):
            return "TIMESTAMP"
    if v.upper() in ("ALLOW", "DENY", "DROP", "REJECT", "ACCEPT", "BLOCK",
                     "LOGIN_FAIL", "LOGIN_SUCCESS", "FILE_ACCESS",
                     "ALLOWED", "DENIED", "BLOCKED"):
        return "ACTION"
    if _QUOTED_PATTERN.match(v):
        return "MESSAGE"
    return "UNKNOWN"


def _analyze_multiline(lines: list) -> dict:
    """
    Handle multi-line custom log formats.
    Each line is treated as a separate field.
    Bracket-wrapped tokens (KEY[value] or KEY[ip#port]) are parsed specially.
    """
    tokens = {}
    data_types = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        field_key = f"field_{i + 1}"
        bracket_match = _BRACKET_PATTERN.match(line)

        if bracket_match:
            label = bracket_match.group(1)   # e.g. "FROM"
            inner = bracket_match.group(2)   # e.g. "192.168.1.1#54321"

            # Check for ip#port pattern inside brackets
            if '#' in inner:
                parts = inner.split('#', 1)
                ip_part, port_part = parts[0].strip(), parts[1].strip()
                if _IP_PATTERN.match(ip_part):
                    tokens[f"{label}_IP"] = ip_part
                    data_types.append("IP")
                    tokens[f"{label}_PORT"] = port_part
                    data_types.append("PORT" if re.match(r'^\d+$', port_part) and 1 <= int(port_part) <= 65535 else "UNKNOWN")
                    continue

            # Bare label[value]
            tokens[label] = inner
            data_types.append(_classify_token(inner))
        else:
            # Strip angle-bracket wrappers like <20260905:143218>
            if line.startswith('<') and line.endswith('>'):
                inner = line[1:-1]
                tokens[field_key] = inner
                data_types.append(_classify_token(inner))
            elif _QUOTED_PATTERN.match(line):
                # Quoted message line
                inner = _QUOTED_PATTERN.match(line).group(1)
                tokens[field_key] = inner
                data_types.append("MESSAGE")
            else:
                tokens[field_key] = line
                data_types.append(_classify_token(line))

    # Build a prefix_pattern from the first line for future matching
    first_line = lines[0].strip() if lines else ""
    prefix_pattern = None
    if first_line.startswith('<') and first_line.endswith('>'):
        prefix_pattern = r'^<\d{8}:\d{6}>'  # e.g. <20260905:143218>

    return {
        "format_type": "multiline_bracketed",
        "delimiter": None,
        "fields": len(tokens),
        "line_count": len([l for l in lines if l.strip()]),
        "data_types": data_types,
        "tokens": tokens,
        "prefix_pattern": prefix_pattern,
    }


def analyze_structure(raw_payload: str) -> dict:
    """
    Analyze an unknown log's structure.
    Returns delimiter, field count, token types, and raw token values.
    Handles both single-line delimited logs and multi-line custom formats.
    """
    lines = [l for l in raw_payload.splitlines() if l.strip()]

    # Multi-line (more than 1 non-empty line) → use multiline analyzer
    if len(lines) > 1:
        return _analyze_multiline(lines)

    # Single-line: try common delimiters
    raw = raw_payload.strip()
    structure = {
        "format_type": "delimited",
        "delimiter": None,
        "fields": 0,
        "line_count": 1,
        "data_types": [],
        "tokens": {},
        "prefix_pattern": None,
    }

    for delim in ['|', '\t', ';']:
        if delim in raw:
            structure["delimiter"] = delim
            break

    if not structure["delimiter"]:
        structure["delimiter"] = " "  # fallback to space

    parts = [p.strip() for p in raw.split(structure["delimiter"]) if p.strip()]
    structure["fields"] = len(parts)

    for i, part in enumerate(parts):
        structure["data_types"].append(_classify_token(part))
        structure["tokens"][f"field_{i + 1}"] = part

    return structure

