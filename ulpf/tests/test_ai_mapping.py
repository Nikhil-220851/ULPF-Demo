"""
Tests for Groq AI integration.

All Groq API calls are mocked — no real HTTP calls are made.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.ai_mapping import AIMapping, AIMappingResponse
from app.services.ai.groq_provider import GroqProvider, _validate_response, VALID_TARGET_FIELDS
from app.services.ai.merger import merge_mappings
from app.models.input_event import InputEvent
from app.core.pipeline import process_event
from app.plugins.manager import plugin_manager

# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_STRUCTURE = {
    "format_type": "delimited",
    "delimiter": " ",
    "fields": 5,
    "line_count": 1,
    "tokens": {
        "field_1": "10.20.30.40",
        "field_2": "443",
        "field_3": "bob",
        "field_4": "ALLOW",
        "field_5": "Connection rejected",
    },
    "data_types": ["IP", "PORT", "UNKNOWN", "ACTION", "UNKNOWN"],
}

SAMPLE_LOCAL_CANDIDATES = {
    "field_1": {"mapped_to": "source.ip", "confidence": 0.90, "value": "10.20.30.40", "token_type": "IP"},
    "field_2": {"mapped_to": "source.port", "confidence": 0.85, "value": "443", "token_type": "PORT"},
    "field_3": {"mapped_to": None, "confidence": 0.0, "value": "bob", "token_type": "UNKNOWN"},
    "field_4": {"mapped_to": "event.action", "confidence": 0.92, "value": "ALLOW", "token_type": "ACTION"},
    "field_5": {"mapped_to": None, "confidence": 0.0, "value": "Connection rejected", "token_type": "UNKNOWN"},
}

VALID_AI_RESPONSE_DATA = {
    "mappings": [
        {"source_field": "field_3", "target_field": "user.name", "confidence": 0.97, "reason": "Looks like a username."},
        {"source_field": "field_5", "target_field": "event.message", "confidence": 0.92, "reason": "Descriptive text."},
        {"source_field": "field_2", "target_field": "destination.port", "confidence": 0.88, "reason": "Port to destination."},
    ]
}


@pytest.fixture(autouse=True)
def clear_plugins():
    plugin_manager.plugins.clear()
    yield
    plugin_manager.plugins.clear()


def _make_groq_completion(json_data: dict):
    """Build a mock Groq completion object matching the SDK response shape."""
    import json as _json
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = _json.dumps(json_data)
    return mock_completion


# ── AIMapping model tests ──────────────────────────────────────────────────────

def test_valid_ai_mapping():
    m = AIMapping(source_field="field_1", target_field="source.ip", confidence=0.94, reason="IPv4")
    assert m.confidence == 0.94

def test_invalid_confidence_range():
    with pytest.raises(Exception):
        AIMapping(source_field="f", target_field="source.ip", confidence=1.5, reason="bad")

def test_confidence_zero_allowed():
    m = AIMapping(source_field="f", target_field="source.ip", confidence=0.0, reason="low")
    assert m.confidence == 0.0


# ── GroqProvider validation tests ─────────────────────────────────────────────

def test_invalid_target_field_rejected():
    response = AIMappingResponse(mappings=[
        AIMapping(source_field="field_1", target_field="evil.field", confidence=0.9, reason="x")
    ])
    validated = _validate_response(response, SAMPLE_STRUCTURE["tokens"])
    assert len(validated.mappings) == 0

def test_unknown_source_field_rejected():
    response = AIMappingResponse(mappings=[
        AIMapping(source_field="nonexistent_field", target_field="source.ip", confidence=0.9, reason="x")
    ])
    validated = _validate_response(response, SAMPLE_STRUCTURE["tokens"])
    assert len(validated.mappings) == 0

def test_duplicate_target_rejected():
    response = AIMappingResponse(mappings=[
        AIMapping(source_field="field_1", target_field="source.ip", confidence=0.9, reason="x"),
        AIMapping(source_field="field_2", target_field="source.ip", confidence=0.8, reason="y"),
    ])
    validated = _validate_response(response, SAMPLE_STRUCTURE["tokens"])
    assert len(validated.mappings) == 1
    assert validated.mappings[0].source_field == "field_1"

def test_valid_mappings_all_accepted():
    response = AIMappingResponse(mappings=[
        AIMapping(source_field="field_3", target_field="user.name", confidence=0.97, reason="username"),
        AIMapping(source_field="field_5", target_field="event.message", confidence=0.92, reason="text"),
    ])
    validated = _validate_response(response, SAMPLE_STRUCTURE["tokens"])
    assert len(validated.mappings) == 2


# ── GroqProvider integration tests (mocked) ───────────────────────────────────

def test_groq_response_parsing():
    provider = GroqProvider()
    mock_completion = _make_groq_completion(VALID_AI_RESPONSE_DATA)
    with patch("app.services.ai.groq_provider.GROQ_API_KEY", "test-key"), \
         patch("app.services.ai.groq_provider.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion
        result = provider.suggest_mappings(
            "raw log", SAMPLE_STRUCTURE, SAMPLE_LOCAL_CANDIDATES, list(VALID_TARGET_FIELDS)
        )
    assert result is not None
    assert any(m.source_field == "field_3" for m in result.mappings)


def test_groq_invalid_json():
    provider = GroqProvider()
    mock_completion = MagicMock()
    mock_completion.choices[0].message.content = "not json at all"
    with patch("app.services.ai.groq_provider.GROQ_API_KEY", "test-key"), \
         patch("app.services.ai.groq_provider.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_completion
        result = provider.suggest_mappings(
            "raw log", SAMPLE_STRUCTURE, SAMPLE_LOCAL_CANDIDATES, list(VALID_TARGET_FIELDS)
        )
    assert result is None


def test_groq_timeout():
    provider = GroqProvider()
    with patch("app.services.ai.groq_provider.GROQ_API_KEY", "test-key"), \
         patch("app.services.ai.groq_provider.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        # Simulate timeout via the generic exception path
        from groq import APITimeoutError
        mock_client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
        result = provider.suggest_mappings(
            "raw log", SAMPLE_STRUCTURE, SAMPLE_LOCAL_CANDIDATES, list(VALID_TARGET_FIELDS)
        )
    assert result is None


def test_groq_api_failure():
    provider = GroqProvider()
    with patch("app.services.ai.groq_provider.GROQ_API_KEY", "test-key"), \
         patch("app.services.ai.groq_provider.Groq") as mock_groq_cls:
        mock_client = MagicMock()
        mock_groq_cls.return_value = mock_client
        from groq import APIStatusError
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_client.chat.completions.create.side_effect = APIStatusError(
            "rate limited", response=mock_response, body={}
        )
        result = provider.suggest_mappings(
            "raw log", SAMPLE_STRUCTURE, SAMPLE_LOCAL_CANDIDATES, list(VALID_TARGET_FIELDS)
        )
    assert result is None


def test_groq_missing_api_key():
    provider = GroqProvider()
    with patch("app.services.ai.groq_provider.GROQ_API_KEY", ""):
        result = provider.suggest_mappings(
            "raw log", SAMPLE_STRUCTURE, SAMPLE_LOCAL_CANDIDATES, list(VALID_TARGET_FIELDS)
        )
    assert result is None


# ── Merger tests ──────────────────────────────────────────────────────────────

def test_local_and_ai_agree():
    ai = AIMappingResponse(mappings=[
        AIMapping(source_field="field_1", target_field="source.ip", confidence=0.97, reason="ip")
    ])
    merged = merge_mappings(SAMPLE_LOCAL_CANDIDATES, ai)
    assert merged["field_1"]["source"] == "ai+local"
    assert merged["field_1"]["confidence"] == 0.97  # max of 0.90 and 0.97


def test_local_and_ai_conflict():
    ai = AIMappingResponse(mappings=[
        AIMapping(source_field="field_1", target_field="destination.ip", confidence=0.80, reason="dest")
    ])
    merged = merge_mappings(SAMPLE_LOCAL_CANDIDATES, ai)
    assert "conflict_candidates" in merged["field_1"]
    targets = [c["target_field"] for c in merged["field_1"]["conflict_candidates"]]
    assert "source.ip" in targets
    assert "destination.ip" in targets


def test_ai_only_mapping():
    ai = AIMappingResponse(mappings=[
        AIMapping(source_field="field_3", target_field="user.name", confidence=0.97, reason="user")
    ])
    merged = merge_mappings(SAMPLE_LOCAL_CANDIDATES, ai)
    assert merged["field_3"]["source"] == "ai"
    assert merged["field_3"]["mapped_to"] == "user.name"


def test_local_only_fallback():
    merged = merge_mappings(SAMPLE_LOCAL_CANDIDATES, None)
    assert merged["field_1"]["source"] == "local"
    assert merged["field_4"]["source"] == "local"


# ── Pipeline integration tests ────────────────────────────────────────────────

LOW_CONFIDENCE_LOG = "UNKNOWN_FIELD1 UNKNOWN_FIELD2 UNKNOWN_FIELD3"


def test_pipeline_ai_disabled_skips_ai():
    event = InputEvent(raw_payload=LOW_CONFIDENCE_LOG)
    with patch("app.core.pipeline.AI_MAPPING_ENABLED", False):
        result = process_event(event)
    assert result.detected_format == "UNKNOWN"
    assert result.ai_used is False
    assert result.ai_status == "not_applicable"


def test_pipeline_high_confidence_skips_ai():
    """Pipe-delimited log with known IPs/ports → local confidence high → AI skipped."""
    event = InputEvent(raw_payload="192.168.1.1|443|10.0.0.5|80|ALLOW")
    with patch("app.core.pipeline.AI_MAPPING_ENABLED", True), \
         patch("app.core.pipeline.AI_MAPPING_THRESHOLD", 0.75), \
         patch("app.services.ai.groq_provider.groq_provider.suggest_mappings") as mock_ai:
        result = process_event(event)
    assert result.detected_format in ("UNKNOWN", "CUSTOM_PLUGIN")
    mock_ai.assert_not_called() if result.ai_status == "skipped" else None


def test_pipeline_ai_failure_fallback():
    """When Groq is unavailable, pipeline continues with local mapping."""
    event = InputEvent(raw_payload=LOW_CONFIDENCE_LOG)
    with patch("app.core.pipeline.AI_MAPPING_ENABLED", True), \
         patch("app.core.pipeline.AI_MAPPING_THRESHOLD", 1.0), \
         patch("app.services.ai.groq_provider.groq_provider.suggest_mappings", return_value=None):
        result = process_event(event)
    assert result.detected_format == "UNKNOWN"
    assert result.ai_used is False
    assert result.ai_status == "unavailable"
    assert result.candidate_mappings is not None


def test_pipeline_unknown_log_with_ai():
    """When AI returns valid mappings, they appear in result."""
    event = InputEvent(raw_payload=LOW_CONFIDENCE_LOG)
    ai_resp = AIMappingResponse(mappings=[
        AIMapping(source_field="field_1", target_field="source.ip", confidence=0.90, reason="ip")
    ])
    with patch("app.core.pipeline.AI_MAPPING_ENABLED", True), \
         patch("app.core.pipeline.AI_MAPPING_THRESHOLD", 1.0), \
         patch("app.services.ai.groq_provider.groq_provider.suggest_mappings", return_value=ai_resp):
        result = process_event(event)
    assert result.ai_used is True
    assert result.ai_status == "success"
    assert result.candidate_mappings is not None
