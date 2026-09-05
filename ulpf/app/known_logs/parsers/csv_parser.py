def parse(raw_payload: str) -> dict:
    parsed = {}
    parts = raw_payload.split(',')
    for i, part in enumerate(parts):
        parsed[f"field_{i+1}"] = part.strip()
    return parsed
