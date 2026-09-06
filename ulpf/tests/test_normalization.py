import pytest
from app.core.normalizer import normalize_event, _parse_composite_endpoint


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
        "source.ip": "1.1.1.1",  # mapped exactly by plugin
        "src_ip": "2.2.2.2"      # generic alias that would normally match
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


# ---------------------------------------------------------------------------
# Regression tests: compound endpoint parsing (bracket + plain, : and #)
# ---------------------------------------------------------------------------

class TestParseCompositeEndpoint:
    """Unit-tests for _parse_composite_endpoint."""

    def test_plain_hash_separator(self):
        ip, port = _parse_composite_endpoint("192.168.44.27#51542")
        assert ip == "192.168.44.27"
        assert port == 51542

    def test_plain_colon_separator(self):
        ip, port = _parse_composite_endpoint("10.20.30.40:443")
        assert ip == "10.20.30.40"
        assert port == 443

    def test_bracket_colon_separator(self):
        ip, port = _parse_composite_endpoint("[172.31.14.22:55120]")
        assert ip == "172.31.14.22"
        assert port == 55120

    def test_bracket_hash_separator(self):
        ip, port = _parse_composite_endpoint("[10.44.8.19#8443]")
        assert ip == "10.44.8.19"
        assert port == 8443

    def test_plain_ip_only(self):
        ip, port = _parse_composite_endpoint("192.168.1.1")
        assert ip == "192.168.1.1"
        assert port is None

    def test_invalid_port_out_of_range(self):
        ip, port = _parse_composite_endpoint("10.0.0.1:99999")
        assert ip is None and port is None

    def test_non_ip_colon(self):
        # hostname:port must NOT be parsed as composite endpoint
        ip, port = _parse_composite_endpoint("example.com:80")
        assert ip is None

    def test_non_string_input(self):
        ip, port = _parse_composite_endpoint(12345)
        assert ip is None and port is None


class TestNormalizeEventCompoundEndpoints:
    """Integration tests: normalize_event with compound endpoint tokens."""

    def test_bracket_colon_source_ip_field(self):
        """[IP:PORT] mapped to source.ip must be split cleanly."""
        event, unmapped = normalize_event({"source.ip": "[172.31.14.22:55120]"})
        assert event.source["ip"] == "172.31.14.22"
        assert event.source["port"] == 55120

    def test_bracket_colon_destination_ip_field(self):
        """[IP:PORT] mapped to destination.ip must be split cleanly."""
        event, unmapped = normalize_event({"destination.ip": "[10.44.8.19:8443]"})
        assert event.destination["ip"] == "10.44.8.19"
        assert event.destination["port"] == 8443

    def test_bracket_hash_source_endpoint_field(self):
        event, unmapped = normalize_event({"source.endpoint": "[192.168.1.5#12345]"})
        assert event.source["ip"] == "192.168.1.5"
        assert event.source["port"] == 12345

    def test_plain_hash_source_ip_field(self):
        event, unmapped = normalize_event({"source.ip": "192.168.44.27#51542"})
        assert event.source["ip"] == "192.168.44.27"
        assert event.source["port"] == 51542

    def test_plain_colon_destination_ip_field(self):
        event, unmapped = normalize_event({"destination.ip": "10.20.30.40:443"})
        assert event.destination["ip"] == "10.20.30.40"
        assert event.destination["port"] == 443

    def test_full_firewall_log_sample(self):
        """
        Regression: FWNODE-A 06-Sep-2026 11:14:03 [172.31.14.22:55120] -> [10.44.8.19:8443] TCP BLOCK user=analyst
        After Groq maps fields, normalizer must split bracket-colon endpoints.
        """
        parsed = {
            "device.hostname": "FWNODE-A",
            "event.timestamp": "06-Sep-2026 11:14:03",
            "source.ip": "[172.31.14.22:55120]",
            "destination.ip": "[10.44.8.19:8443]",
            "network.transport": "TCP",
            "event.action": "BLOCK",
            "user.name": "analyst",
        }
        event, unmapped = normalize_event(parsed)
        assert event.source["ip"] == "172.31.14.22"
        assert event.source["port"] == 55120
        assert event.destination["ip"] == "10.44.8.19"
        assert event.destination["port"] == 8443
        assert event.network.get("transport") == "tcp"
        assert event.user.get("name") == "analyst"
