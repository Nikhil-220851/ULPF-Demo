import json
import re

from app.known_logs.parsers import cef_parser, json_parser, syslog_parser, leef_parser, keyvalue_parser, csv_parser

def detect_format(raw_payload: str) -> dict:
    raw = raw_payload.strip()
    
    # JSON
    if raw.startswith("{") and raw.endswith("}"):
        try:
            json.loads(raw)
            return {"format": "JSON", "parser": json_parser.parse, "parser_name": "JSONParser"}
        except:
            pass
            
    # CEF
    if raw.startswith("CEF:"):
        return {"format": "CEF", "parser": cef_parser.parse, "parser_name": "CEFParser"}
        
    # LEEF
    if raw.startswith("LEEF:"):
        return {"format": "LEEF", "parser": leef_parser.parse, "parser_name": "LEEFParser"}
        
    # Syslog (RFC3164 / RFC5424 heuristic)
    if re.match(r'^<\d+>', raw) or re.match(r'^[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2}', raw):
        return {"format": "SYSLOG", "parser": syslog_parser.parse, "parser_name": "SyslogParser"}
        
    # Key-Value (simple heuristic: contains multiple a=b)
    if "=" in raw and not "|" in raw:
        # Check if it has multiple key=value pairs
        if len(re.findall(r'\b\w+=', raw)) > 1:
            return {"format": "KEYVALUE", "parser": keyvalue_parser.parse, "parser_name": "KeyValueParser"}
            
    # CSV (comma separated, at least 2 commas, no obvious other structure)
    if "," in raw and not "=" in raw and not "|" in raw:
        if raw.count(",") >= 2:
            return {"format": "CSV", "parser": csv_parser.parse, "parser_name": "CSVParser"}
            
    # Stored Custom Plugins
    from app.plugins.manager import plugin_manager
    from app.plugins.parser import parse_with_plugin
    from app.unknown_logs.structure_analyzer import analyze_structure
    
    structure = analyze_structure(raw)
    matched_plugin = plugin_manager.match_plugin(raw, structure)
    if matched_plugin:
        return {
            "format": "CUSTOM_PLUGIN", 
            "parser": lambda r: parse_with_plugin(r, matched_plugin), 
            "parser_name": matched_plugin.get("name", "CustomPlugin")
        }
            
    return {"format": "UNKNOWN", "parser": None}
