import pytest
from app.core.normalizer import normalize_event

def test_source_ip_normalization():
    input_data = {
        "src_ip": "192.168.1.10",
        "clientaddress": "10.0.0.5"
    }
    event, unmapped = normalize_event(input_data)
    assert event.source["ip"] == "192.168.1.10"
    assert "clientaddress" in unmapped
    assert unmapped["clientaddress"] == "10.0.0.5"

def test_destination_ip_normalization():
    input_data = {
        "destination_address": "8.8.8.8"
    }
    event, unmapped = normalize_event(input_data)
    assert event.destination["ip"] == "8.8.8.8"
    assert len(unmapped) == 0

def test_port_normalization_and_conversion():
    input_data = {
        "spt": "54321",
        "dport": 443,
        "src_port": "invalid"
    }
    event, unmapped = normalize_event(input_data)
    assert event.source["port"] == 54321
    assert event.destination["port"] == 443
    # Conflict for source port - 'spt' takes precedence due to order or whichever matched first,
    # wait, the order is based on dictionary iteration.
    # In python 3.7+ dict iteration order is insertion order.
    # 'spt' is first, so it gets mapped to source.port
    # 'src_port' should be unmapped.
    assert "src_port" in unmapped
    assert unmapped["src_port"] == "invalid"

def test_protocol_normalization():
    input_data = {
        "proto": "TCP",
        "network_protocol": "UDP"
    }
    event, unmapped = normalize_event(input_data)
    assert event.network["transport"] == "tcp"
    assert "network_protocol" in unmapped

def test_user_normalization():
    input_data = {
        "duser": "admin"
    }
    event, unmapped = normalize_event(input_data)
    assert event.user["name"] == "admin"
    assert len(unmapped) == 0

def test_message_normalization():
    input_data = {
        "description": "User logged in"
    }
    event, unmapped = normalize_event(input_data)
    assert event.event["message"] == "User logged in"

def test_timestamp_normalization():
    input_data = {
        "time": "2026-09-05 10:30:00",
        "created_at": "invalid_date"
    }
    event, unmapped = normalize_event(input_data)
    assert event.event["timestamp"] == "2026-09-05T10:30:00"
    assert unmapped["created_at"] == "invalid_date"

def test_case_variations():
    input_data = {
        "SOURCE_IP": "10.0.0.1",
        "SourceIp": "10.0.0.2"
    }
    event, unmapped = normalize_event(input_data)
    assert event.source["ip"] == "10.0.0.1"
    assert unmapped["SourceIp"] == "10.0.0.2"

def test_unknown_fields_preserved():
    input_data = {
        "weird_internal_code": "ABC123",
        "src": "10.0.0.1"
    }
    event, unmapped = normalize_event(input_data)
    assert event.source["ip"] == "10.0.0.1"
    assert unmapped["weird_internal_code"] == "ABC123"

def test_plugin_mapping_precedence():
    input_data = {
        "source.ip": "1.1.1.1", # mapped exactly by plugin
        "src_ip": "2.2.2.2"     # generic alias that would normally match
    }
    event, unmapped = normalize_event(input_data)
    assert event.source["ip"] == "1.1.1.1"
    assert unmapped["src_ip"] == "2.2.2.2"

def test_nested_output_structure():
    input_data = {
        "src_ip": "10.0.0.1",
        "spt": "1234"
    }
    event, unmapped = normalize_event(input_data)
    assert event.source == {"ip": "10.0.0.1", "port": 1234}
    assert event.destination == {}
