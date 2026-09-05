import json

def parse(raw_payload: str) -> dict:
    try:
        return json.loads(raw_payload)
    except:
        return {}
