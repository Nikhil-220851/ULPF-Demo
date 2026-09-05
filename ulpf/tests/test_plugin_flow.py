import pytest
from app.core.pipeline import process_event
from app.models.input_event import InputEvent
from app.plugins.manager import plugin_manager
import json

MULTILINE_LOG = """<20260905:143218>
FROM_IP[192.168.50.23]
TO_IP[10.0.0.5]
TO_PORT[443]
USER[jsmith]
ACTION[ALLOW]"""

@pytest.fixture(autouse=True)
def clear_plugins():
    plugin_manager.plugins.clear()
    yield
    plugin_manager.plugins.clear()


def test_unknown_log_produces_structure_and_candidates():
    # Test A
    event = InputEvent(raw_payload=MULTILINE_LOG, source_file="test.log", source_file_index=1)
    result = process_event(event)

    assert result.detected_format == "UNKNOWN"
    
    assert result.structure is not None
    assert result.structure["format_type"] == "multiline_bracketed"
    assert result.structure["fields"] == 6
    assert result.structure["line_count"] == 6
    assert result.structure["delimiter"] is None
    
    assert result.candidate_mappings is not None
    assert "FROM_IP" in result.candidate_mappings
    assert result.candidate_mappings["FROM_IP"]["mapped_to"] == "source.ip"
    assert result.candidate_mappings["TO_IP"]["mapped_to"] == "destination.ip"
    assert result.candidate_mappings["ACTION"]["mapped_to"] == "event.action"


def test_plugin_confirmation_flow():
    # Test B
    event = InputEvent(raw_payload=MULTILINE_LOG, source_file="test.log", source_file_index=1)
    result = process_event(event)
    
    # Simulate frontend confirm
    plugin_def = {
        "plugin_id": "test_plugin",
        "name": "Test Plugin",
        "signature": {
            "format_type": result.structure["format_type"],
            "delimiter": result.structure["delimiter"],
            "field_count": result.structure["fields"],
            "line_count": result.structure["line_count"],
            "prefix_pattern": result.structure["prefix_pattern"]
        },
        "field_mappings": {}
    }
    for field, info in result.candidate_mappings.items():
        if info["mapped_to"]:
            plugin_def["field_mappings"][field] = info["mapped_to"]
            
    saved = plugin_manager.save_plugin(plugin_def)
    assert saved is True
    
    # Process again
    result2 = process_event(event)
    assert result2.detected_format == "CUSTOM_PLUGIN"
    assert result2.parser == "Test Plugin"
    
    assert result2.normalized_event.source["ip"] == "192.168.50.23"
    assert result2.normalized_event.destination["ip"] == "10.0.0.5"
    assert result2.normalized_event.destination["port"] == 443
    assert result2.normalized_event.user["name"] == "jsmith"
    assert result2.normalized_event.event["action"] == "ALLOW"
    assert result2.normalized_event.event["timestamp"] == "20260905:143218"
