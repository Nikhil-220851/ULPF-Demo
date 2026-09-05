import pytest
from app.models.input_event import InputEvent
from app.core.pipeline import process_event
from app.core.ocsf.constants import OCSF_VERSION

# Sample Logs
CEF_LOG = "CEF:0|PaloAlto|Firewall|11.0|1001|Network Traffic|5|src=192.168.1.30 dst=10.0.0.10 spt=8080 dpt=443 proto=TCP act=ALLOW"
JSON_LOG = '{"source_ip": "192.168.1.20", "destination_ip": "10.0.0.8", "source_port": 22, "destination_port": 443, "protocol": "TCP", "action": "DENY"}'
SYSLOG_LOG = "<34>Oct 11 22:14:15 mymachine su: 'su root' failed for lonvick on /dev/pts/8"
UNKNOWN_LOG = "172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP"

def test_cef_to_ocsf():
    event = InputEvent(raw_payload=CEF_LOG, source_file="test.log", source_file_index=1)
    result = process_event(event)
    
    assert result.validation["status"] == "VALID"
    assert result.ocsf_validation["status"] == "VALID"
    assert result.detected_format == "CEF"
    
    ocsf = result.ocsf
    assert ocsf is not None
    assert ocsf["metadata"]["version"] == OCSF_VERSION
    assert ocsf["class_uid"] == 4001
    
    assert ocsf["src_endpoint"]["ip"] == "192.168.1.30"
    assert ocsf["src_endpoint"]["port"] == 8080
    assert ocsf["dst_endpoint"]["ip"] == "10.0.0.10"
    assert ocsf["dst_endpoint"]["port"] == 443
    assert ocsf["connection_info"]["protocol_name"] == "tcp"
    assert ocsf["activity_id"] == 1 # ALLOW
    
def test_json_to_ocsf():
    event = InputEvent(raw_payload=JSON_LOG)
    result = process_event(event)
    
    assert result.validation["status"] == "VALID"
    assert result.ocsf_validation["status"] == "VALID"
    assert result.detected_format == "JSON"
    
    ocsf = result.ocsf
    assert ocsf["src_endpoint"]["ip"] == "192.168.1.20"
    assert ocsf["src_endpoint"]["port"] == 22
    assert ocsf["dst_endpoint"]["ip"] == "10.0.0.8"
    assert ocsf["dst_endpoint"]["port"] == 443
    assert ocsf["connection_info"]["protocol_name"] == "tcp"
    assert ocsf["activity_id"] == 2 # DENY
    
def test_syslog_to_ocsf():
    event = InputEvent(raw_payload=SYSLOG_LOG)
    result = process_event(event)
    
    # Syslog might not have IPs parsed cleanly into source/dest depending on ULPF current regex
    # But it should still produce a valid OCSF wrapper
    assert result.ocsf_validation["status"] == "VALID"
    assert result.detected_format == "SYSLOG"
    assert result.ocsf["class_uid"] == 4001
    
def test_unknown_to_ocsf():
    event = InputEvent(raw_payload=UNKNOWN_LOG)
    result = process_event(event)
    
    # UNKNOWN will be mapped by Adaptive Intelligence
    # Since it's a pipe separated, it might map some fields
    # Should not fail OCSF validation as long as format of mapped IP is fine
    assert result.ocsf_validation["status"] == "VALID"
    assert result.detected_format == "UNKNOWN"

def test_missing_field_behavior():
    # Provide IP but no ports
    log = '{"source_ip": "192.168.1.20", "destination_ip": "10.0.0.8"}'
    event = InputEvent(raw_payload=log)
    result = process_event(event)
    
    assert result.ocsf_validation["status"] == "VALID"
    ocsf = result.ocsf
    assert "port" not in ocsf.get("src_endpoint", {})
    assert "port" not in ocsf.get("dst_endpoint", {})
    
def test_unmapped_field_preservation():
    log = '{"source_ip": "192.168.1.20", "weird_field": "xyz123"}'
    event = InputEvent(raw_payload=log)
    result = process_event(event)
    
    assert result.ocsf_validation["status"] == "VALID"
    # weird_field should be in unmapped_fields
    assert "weird_field" in result.unmapped_fields
    assert result.unmapped_fields["weird_field"] == "xyz123"
    
def test_raw_event_preservation():
    event = InputEvent(raw_payload=CEF_LOG)
    result = process_event(event)
    assert result.raw_event == CEF_LOG

def test_syslog_ocsf_not_empty_regression():
    """
    Regression: live Syslog event must produce a non-empty OCSF object.
    Previously showed {} and 'OCSF Invalid' in the UI because the
    server was running stale pre-OCSF code. This test pins the behavior
    for the fully-integrated pipeline path.
    """
    syslog = "Sep 05 09:15:22 firewall01 SRCIP=192.168.10.25 DSTIP=10.0.0.5 SRCPORT=443 DSTPORT=52144 PROTO=TCP ACTION=ALLOW SEVERITY=5"
    event = InputEvent(raw_payload=syslog)
    result = process_event(event)

    # Must produce an OCSF object — not None and not {}
    assert result.ocsf is not None
    assert result.ocsf != {}

    # Must pass validation
    assert result.ocsf_validation["status"] == "VALID"

    # Class and category must be correct
    assert result.ocsf["class_uid"] == 4001
    assert result.ocsf["category_uid"] == 4

    # Key fields must be mapped
    assert result.ocsf["src_endpoint"]["ip"] == "192.168.10.25"
    assert result.ocsf["dst_endpoint"]["ip"] == "10.0.0.5"
    assert result.ocsf["src_endpoint"]["port"] == 443
    assert result.ocsf["dst_endpoint"]["port"] == 52144
    assert result.ocsf["connection_info"]["protocol_name"] == "tcp"
    assert result.ocsf["activity_id"] == 1       # ALLOW
    assert result.ocsf["time_dt"] == "2026-09-05T09:15:22"

    # Raw event must be fully preserved
    assert result.raw_event == syslog
    
def test_ocsf_validation_failure_surfaces():
    """
    OCSF validation failures must surface through ocsf_validation.status == 'INVALID'
    while the full event (raw log, provenance, normalized data) remains lossless.
    The pipeline does NOT hard-quarantine on OCSF validation failure — it preserves
    all context so the consumer can inspect and decide.
    """
    log = '{"source_ip": "invalid_ip_address", "destination_ip": "10.0.0.8"}'
    event = InputEvent(raw_payload=log)
    result = process_event(event)

    # Event was still fully processed — not lost
    assert result.raw_event == log
    assert result.detected_format == "JSON"

    # OCSF validation failure is visible
    assert result.ocsf_validation is not None
    assert result.ocsf_validation["status"] == "INVALID"
    assert any("Invalid source IP" in e for e in result.ocsf_validation["errors"])

    # Core ULPF validation is separate — not affected by OCSF issue
    # (the ULPF validator checks its own constraints, not OCSF ones)
    assert "status" in result.validation
