"""
Tests for Unknown Log AI Structure & Delimiter Discovery,
Delimiter Exclude, Composite Value Normalization, and Plugin Workflow.
"""
import pytest
from unittest.mock import patch
from app.models.input_event import InputEvent
from app.core.pipeline import process_event
from app.models.ai_mapping import AIMappingResponse, AIMapping


def test_unknown_log_double_colon_delimiter():
    """TEST A: Groq / Structure discovery identifies :: delimiter and 7 fields without treating :: as fields."""
    raw = "GW-ALPHA :: 2026/09/05 17:42:31 :: 192.168.44.27#51542 :: 10.20.30.40#443 :: TCP :: BLOCK :: analyst"
    
    mock_ai = AIMappingResponse(
        format_name="Custom Gateway Firewall Log",
        format_type="delimited",
        delimiter="::",
        confidence=0.98,
        mappings=[
            AIMapping(source_field="field_1", target_field="device.hostname", confidence=0.99, sample_value="GW-ALPHA"),
            AIMapping(source_field="field_2", target_field="event.timestamp", confidence=0.99, sample_value="2026/09/05 17:42:31"),
            AIMapping(source_field="field_3", target_field="source.ip", confidence=0.99, sample_value="192.168.44.27#51542"),
            AIMapping(source_field="field_4", target_field="destination.ip", confidence=0.99, sample_value="10.20.30.40#443"),
            AIMapping(source_field="field_5", target_field="network.transport", confidence=0.99, sample_value="TCP"),
            AIMapping(source_field="field_6", target_field="event.action", confidence=0.98, sample_value="BLOCK"),
            AIMapping(source_field="field_7", target_field="user.name", confidence=0.95, sample_value="analyst"),
        ]
    )

    with patch("app.services.ai.groq_provider.groq_provider.suggest_mappings", return_value=mock_ai):
        event = InputEvent(raw_payload=raw)
        result = process_event(event)

    assert result.detected_format == "UNKNOWN"
    assert result.ai_used is True
    assert result.ai_status == "success"
    assert result.structure["delimiter"] == "::"
    assert result.structure["fields"] == 7

    # Ensure delimiter is not present as a token value
    tokens = result.structure["tokens"]
    for val in tokens.values():
        assert val != "::"

    # Normalized checks
    norm = result.normalized_event
    assert norm.device["hostname"] == "GW-ALPHA"
    assert norm.source["ip"] == "192.168.44.27"
    assert norm.source["port"] == 51542
    assert norm.destination["ip"] == "10.20.30.40"
    assert norm.destination["port"] == 443
    assert norm.network["transport"] == "tcp"
    assert norm.event["action"] == "BLOCK"
    assert norm.user["name"] == "analyst"


def test_unknown_log_pipe_delimiter():
    """TEST C: Unknown log with | delimiter."""
    raw = "GW-BETA | 2026-09-05 18:01:22 | 10.0.0.10#5000 | 172.16.1.20#443 | TCP | DENY | admin"
    
    mock_ai = AIMappingResponse(
        format_name="Pipe Custom Log",
        format_type="delimited",
        delimiter="|",
        confidence=0.96,
        mappings=[
            AIMapping(source_field="field_1", target_field="device.hostname", confidence=0.99, sample_value="GW-BETA"),
            AIMapping(source_field="field_2", target_field="event.timestamp", confidence=0.99, sample_value="2026-09-05 18:01:22"),
            AIMapping(source_field="field_3", target_field="source.ip", confidence=0.99, sample_value="10.0.0.10#5000"),
            AIMapping(source_field="field_4", target_field="destination.ip", confidence=0.99, sample_value="172.16.1.20#443"),
            AIMapping(source_field="field_5", target_field="network.transport", confidence=0.99, sample_value="TCP"),
            AIMapping(source_field="field_6", target_field="event.action", confidence=0.98, sample_value="DENY"),
            AIMapping(source_field="field_7", target_field="user.name", confidence=0.95, sample_value="admin"),
        ]
    )

    with patch("app.services.ai.groq_provider.groq_provider.suggest_mappings", return_value=mock_ai):
        event = InputEvent(raw_payload=raw)
        result = process_event(event)

    assert result.ai_used is True
    assert result.structure["delimiter"] == "|"
    assert result.normalized_event.source["ip"] == "10.0.0.10"
    assert result.normalized_event.source["port"] == 5000
    assert result.normalized_event.destination["ip"] == "172.16.1.20"
    assert result.normalized_event.destination["port"] == 443


def test_groq_failure_fallback():
    """TEST D: Groq failure gracefully falls back to regex structure analysis."""
    raw = "GW-ALPHA :: 2026/09/05 17:42:31 :: 192.168.44.27#51542 :: 10.20.30.40#443 :: TCP :: BLOCK :: analyst"

    with patch("app.services.ai.groq_provider.groq_provider.suggest_mappings", return_value=None):
        event = InputEvent(raw_payload=raw)
        result = process_event(event)

    assert result.detected_format == "UNKNOWN"
    assert result.ai_used is False
    assert result.ai_status == "unavailable"
    assert result.structure["structure_source"] == "regex"
    assert result.structure["delimiter"] == "::"
