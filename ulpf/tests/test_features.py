"""
Comprehensive tests for:
  - Plugin creation, persistence, matching, and generic parsing
  - Quarantine: invalid events, raw preservation, isolation
  - Multi-file: source provenance, event counts, error isolation
"""

import json
import os
import shutil
import pytest
from fastapi.testclient import TestClient

# ─── Setup ───────────────────────────────────────────────────────────────────
PLUGINS_STORAGE = os.path.join(
    os.path.dirname(__file__), "..", "app", "plugins", "storage"
)

@pytest.fixture(autouse=True)
def clean_plugins():
    """Remove any test-created plugins before and after each test."""
    test_ids = []
    yield test_ids
    for pid in test_ids:
        fpath = os.path.join(PLUGINS_STORAGE, f"{pid}.json")
        if os.path.exists(fpath):
            os.remove(fpath)

def _make_client():
    from app.plugins.manager import plugin_manager
    plugin_manager.load_plugins()   # reload to pick up any state changes
    from app.main import app
    return TestClient(app)

# ─── Quarantine Tests ─────────────────────────────────────────────────────────

class TestQuarantine:
    def test_valid_event_is_valid(self):
        client = _make_client()
        r = client.post("/process", json={"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 ACTION=ALLOW"})
        assert r.status_code == 200
        assert r.json()["validation"]["status"] == "VALID"

    def test_invalid_ip_quarantined(self):
        client = _make_client()
        r = client.post("/process", json={"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=999.999.999.999 DSTIP=10.0.0.5 ACTION=ALLOW"})
        assert r.status_code == 200
        data = r.json()
        assert data["validation"]["status"] != "VALID"

    def test_raw_event_preserved_after_quarantine(self):
        client = _make_client()
        raw = "src=999.0.0.1 dst=10.0.0.5 act=ALLOW"
        r = client.post("/process", json={"raw_payload": raw})
        assert r.status_code == 200
        assert r.json()["raw_event"] == raw

    def test_malformed_in_batch_isolates_others(self):
        client = _make_client()
        events = [
            "Sep 05 10:01:12 fw01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 ACTION=ALLOW",
            "Sep 05 10:01:12 fw01 SRCIP=999.999.999.999 DSTIP=10.0.0.5 ACTION=ALLOW",
            '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","action":"DENY"}',
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        data = r.json()
        assert data["processed"] == 3
        statuses = [res["validation"]["status"] for res in data["results"]]
        assert statuses[0] == "VALID"
        assert statuses[1] != "VALID"
        assert statuses[2] == "VALID"

    def test_event_id_present(self):
        client = _make_client()
        r = client.post("/process", json={"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW"})
        assert r.status_code == 200
        assert r.json().get("event_id")

    def test_source_file_preserved(self):
        client = _make_client()
        r = client.post("/process/batch", json={
            "events": [{"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW", "source_file": "firewall.log", "source_file_index": 0}]
        })
        assert r.status_code == 200
        result = r.json()["results"][0]
        assert result["source_file"] == "firewall.log"
        assert result["source_file_index"] == 0


# ─── Plugin Tests ─────────────────────────────────────────────────────────────

PIPE_EVENT_1 = "172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP"
PIPE_EVENT_2 = "172.16.50.22|10.10.20.16|53110|80|ALLOW|TCP"
PIPE_EVENT_NO_MATCH = "172.16.50.21|10.10.20.15|54321|DENY|TCP"  # only 5 fields

PIPE_PLUGIN_SIGNATURE = {
    "delimiter": "|",
    "field_count": 6,
    "field_types": ["IP", "IP", "PORT", "PORT", "ACTION", "PROTOCOL"],
}
PIPE_FIELD_MAPPINGS = {
    "0": "source.ip",
    "1": "destination.ip",
    "2": "source.port",
    "3": "destination.port",
    "4": "event.action",
    "5": "network.protocol",
}


class TestPlugin:
    def test_unknown_detected_before_plugin(self):
        """Before creating a plugin, pipe-delimited event is UNKNOWN."""
        client = _make_client()
        r = client.post("/process", json={"raw_payload": PIPE_EVENT_1})
        assert r.status_code == 200
        assert r.json()["detected_format"] == "UNKNOWN"

    def test_confirm_plugin_creates_file(self, clean_plugins):
        client = _make_client()
        r = client.post("/plugins/confirm", json={
            "name": "Test Pipe Plugin",
            "signature": PIPE_PLUGIN_SIGNATURE,
            "field_mappings": PIPE_FIELD_MAPPINGS,
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"
        plugin = data["plugin"]
        pid = plugin["plugin_id"]
        clean_plugins.append(pid)

        # File must exist on disk
        fpath = os.path.join(PLUGINS_STORAGE, f"{pid}.json")
        assert os.path.exists(fpath)
        with open(fpath) as f:
            saved = json.load(f)
        assert saved["plugin_id"] == pid
        assert saved["enabled"] is True

    def test_plugin_listed_via_api(self, clean_plugins):
        client = _make_client()
        r = client.post("/plugins/confirm", json={
            "name": "Listed Plugin",
            "signature": {"delimiter": ";", "field_count": 3},
            "field_mappings": {"0": "source.ip"},
        })
        pid = r.json()["plugin"]["plugin_id"]
        clean_plugins.append(pid)

        r2 = client.get("/plugins")
        assert r2.status_code == 200
        ids = [p["plugin_id"] for p in r2.json()]
        assert pid in ids

    def test_second_event_uses_plugin(self, clean_plugins):
        """After confirming, a structurally-matching event should be CUSTOM_PLUGIN."""
        from app.plugins.manager import plugin_manager

        # Directly save plugin so we control the id
        pid = "test_pipe_fw_match"
        plugin_def = {
            "plugin_id": pid,
            "name": "Test Pipe FW",
            "version": "1.0",
            "signature": PIPE_PLUGIN_SIGNATURE,
            "field_mappings": PIPE_FIELD_MAPPINGS,
            "created_by": "human-confirmed",
            "confidence": 1.0,
            "enabled": True,
        }
        plugin_manager.save_plugin(plugin_def)
        clean_plugins.append(pid)
        plugin_manager.load_plugins()

        client = _make_client()
        r = client.post("/process", json={"raw_payload": PIPE_EVENT_2})
        assert r.status_code == 200
        data = r.json()
        assert data["detected_format"] == "CUSTOM_PLUGIN", f"Expected CUSTOM_PLUGIN, got {data['detected_format']}"
        assert data["validation"]["status"] == "VALID"

    def test_plugin_normalizes_fields(self, clean_plugins):
        from app.plugins.manager import plugin_manager

        pid = "test_pipe_norm"
        plugin_manager.save_plugin({
            "plugin_id": pid, "name": "Norm Plugin", "version": "1.0",
            "signature": PIPE_PLUGIN_SIGNATURE,
            "field_mappings": PIPE_FIELD_MAPPINGS,
            "created_by": "human-confirmed", "confidence": 1.0, "enabled": True,
        })
        clean_plugins.append(pid)
        plugin_manager.load_plugins()

        client = _make_client()
        r = client.post("/process", json={"raw_payload": PIPE_EVENT_2})
        assert r.status_code == 200
        norm = r.json()["normalized_event"]
        assert norm.get("source", {}).get("ip") is not None
        assert norm.get("destination", {}).get("ip") is not None

    def test_non_matching_event_not_captured_by_plugin(self, clean_plugins):
        """5-field event must not match a 6-field plugin."""
        from app.plugins.manager import plugin_manager

        pid = "test_pipe_nomatch"
        plugin_manager.save_plugin({
            "plugin_id": pid, "name": "NoMatch Plugin", "version": "1.0",
            "signature": PIPE_PLUGIN_SIGNATURE,
            "field_mappings": PIPE_FIELD_MAPPINGS,
            "created_by": "human-confirmed", "confidence": 1.0, "enabled": True,
        })
        clean_plugins.append(pid)
        plugin_manager.load_plugins()

        client = _make_client()
        r = client.post("/process", json={"raw_payload": PIPE_EVENT_NO_MATCH})
        assert r.status_code == 200
        # Should NOT be CUSTOM_PLUGIN (5 fields vs 6 in signature)
        assert r.json()["detected_format"] != "CUSTOM_PLUGIN"

    def test_plugin_persists_after_reload(self, clean_plugins):
        """Plugin loaded from disk after plugin_manager.load_plugins()."""
        from app.plugins.manager import plugin_manager

        pid = "test_pipe_persist"
        plugin_manager.save_plugin({
            "plugin_id": pid, "name": "Persist Plugin", "version": "1.0",
            "signature": PIPE_PLUGIN_SIGNATURE,
            "field_mappings": PIPE_FIELD_MAPPINGS,
            "created_by": "human-confirmed", "confidence": 1.0, "enabled": True,
        })
        clean_plugins.append(pid)

        # Reload from disk
        plugin_manager.plugins.clear()
        plugin_manager.load_plugins()

        assert pid in plugin_manager.plugins


# ─── Multi-File Tests ─────────────────────────────────────────────────────────

class TestMultiFile:
    def test_source_file_in_result(self):
        client = _make_client()
        events = [
            {"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW", "source_file": "fw.log", "source_file_index": 0},
            {"raw_payload": '{"source_ip":"10.0.0.1","destination_ip":"10.0.0.2","action":"DENY"}', "source_file": "events.json", "source_file_index": 1},
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        results = r.json()["results"]
        assert results[0]["source_file"] == "fw.log"
        assert results[1]["source_file"] == "events.json"

    def test_multiple_files_correct_count(self):
        client = _make_client()
        events = [
            {"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW", "source_file": "file1.log"},
            {"raw_payload": "CEF:0|Vendor|Product|1.0|100|Name|5|src=1.2.3.4 dst=5.6.7.8 act=ALLOW", "source_file": "file2.log"},
            {"raw_payload": '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","action":"DENY"}', "source_file": "file3.json"},
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        assert data["processed"] == 3

    def test_malformed_in_one_file_does_not_stop_others(self):
        client = _make_client()
        events = [
            {"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW", "source_file": "file1.log"},
            {"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=999.999.999.999 DSTIP=10.0.0.1 ACTION=ALLOW", "source_file": "file2.log"},
            {"raw_payload": "CEF:0|Vendor|Product|1.0|100|Name|5|src=1.2.3.4 dst=5.6.7.8 act=ALLOW", "source_file": "file3.log"},
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        data = r.json()
        assert data["processed"] == 3
        statuses = [res["validation"]["status"] for res in data["results"]]
        assert statuses[0] == "VALID"
        assert statuses[1] != "VALID"   # quarantined
        assert statuses[2] == "VALID"

    def test_mixed_formats_across_files(self):
        client = _make_client()
        events = [
            {"raw_payload": "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW", "source_file": "fw.log"},
            {"raw_payload": '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","action":"DENY"}', "source_file": "events.json"},
            {"raw_payload": "CEF:0|Vendor|Product|1.0|100|Name|5|src=1.2.3.4 dst=5.6.7.8 act=ALLOW", "source_file": "cef.log"},
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        results = r.json()["results"]
        assert results[0]["detected_format"] == "SYSLOG"
        assert results[1]["detected_format"] == "JSON"
        assert results[2]["detected_format"] == "CEF"

    def test_raw_event_preserved_per_event(self):
        client = _make_client()
        raw1 = "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW"
        raw2 = '{"source_ip":"10.0.0.1","action":"DENY"}'
        events = [
            {"raw_payload": raw1, "source_file": "a.log"},
            {"raw_payload": raw2, "source_file": "b.json"},
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        results = r.json()["results"]
        assert results[0]["raw_event"] == raw1
        assert results[1]["raw_event"] == raw2

    def test_backward_compat_string_events(self):
        """Legacy string-only batch payload must still work."""
        client = _make_client()
        events = [
            "Sep 05 10:01:12 fw01 SRCIP=192.168.1.1 DSTIP=10.0.0.1 ACTION=ALLOW",
            '{"source_ip":"10.0.0.1","action":"DENY"}',
        ]
        r = client.post("/process/batch", json={"events": events})
        assert r.status_code == 200
        assert r.json()["processed"] == 2
