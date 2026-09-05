from fastapi.testclient import TestClient
from app.main import app
from app.models.input_event import BatchInput, InputEvent

client = TestClient(app)

def test_mixed_6_event_batch():
    events = [
        "Sep 05 10:01:12 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 SRCPORT=443 DSTPORT=52144 PROTO=TCP ACTION=ALLOW SEVERITY=5",
        '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","source_port":22,"destination_port":443,"protocol":"TCP","action":"DENY"}',
        "CEF:0|PaloAlto|Firewall|11.0|1001|Network Traffic|5|src=192.168.1.30 dst=10.0.0.10 spt=8080 dpt=443 proto=TCP act=ALLOW",
        "172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP",
        "Sep 05 10:04:51 firewall02 SRCIP=10.1.1.15 DSTIP=192.168.10.20 SRCPORT=3389 DSTPORT=49152 PROTO=TCP ACTION=DENY SEVERITY=8",
        '{"source_ip":"10.2.2.10","destination_ip":"172.16.1.50","source_port":53,"destination_port":53000,"protocol":"UDP","action":"ALLOW"}'
    ]
    
    response = client.post("/process/batch", json={"events": events})
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 6
    assert data["processed"] == 6
    results = data["results"]
    assert len(results) == 6
    
    # Event 1
    assert results[0]["detected_format"] == "SYSLOG"
    assert results[0]["parser"] == "SyslogParser"
    assert results[0]["validation"]["status"] == "VALID"
    assert results[0]["raw_event"] == events[0]
    
    # Event 2
    assert results[1]["detected_format"] == "JSON"
    assert results[1]["parser"] == "JSONParser"
    assert results[1]["validation"]["status"] == "VALID"
    assert results[1]["raw_event"] == events[1]
    
    # Event 3
    assert results[2]["detected_format"] == "CEF"
    assert results[2]["parser"] == "CEFParser"
    assert results[2]["validation"]["status"] == "VALID"
    assert results[2]["raw_event"] == events[2]
    
    # Event 4
    assert results[3]["detected_format"] == "UNKNOWN"
    assert results[3]["parser"] == "Adaptive Intelligence"
    assert results[3]["validation"]["status"] == "VALID"
    assert results[3]["raw_event"] == events[3]
    assert results[3]["confidence"]["overall"] < 1.0 # Should be low confidence mapping
    
    # Event 5
    assert results[4]["detected_format"] == "SYSLOG"
    assert results[4]["parser"] == "SyslogParser"
    assert results[4]["validation"]["status"] == "VALID"
    assert results[4]["raw_event"] == events[4]
    
    # Event 6
    assert results[5]["detected_format"] == "JSON"
    assert results[5]["parser"] == "JSONParser"
    assert results[5]["validation"]["status"] == "VALID"
    assert results[5]["raw_event"] == events[5]

def test_single_syslog():
    event = "Sep 05 10:01:12 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 ACTION=ALLOW"
    response = client.post("/process", json={"raw_payload": event})
    assert response.status_code == 200
    data = response.json()
    assert data["detected_format"] == "SYSLOG"
    assert data["parser"] == "SyslogParser"

def test_single_json():
    event = '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","action":"DENY"}'
    response = client.post("/process", json={"raw_payload": event})
    assert response.status_code == 200
    data = response.json()
    assert data["detected_format"] == "JSON"
    assert data["parser"] == "JSONParser"

def test_single_cef():
    event = "CEF:0|VendorX|Firewall|1.0|100|Network Traffic|5|src=192.168.1.30 dst=10.0.0.10 act=ALLOW"
    response = client.post("/process", json={"raw_payload": event})
    assert response.status_code == 200
    data = response.json()
    assert data["detected_format"] == "CEF"
    assert data["parser"] == "CEFParser"

def test_single_unknown():
    event = "172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP"
    response = client.post("/process", json={"raw_payload": event})
    assert response.status_code == 200
    data = response.json()
    assert data["detected_format"] == "UNKNOWN"
    assert data["parser"] == "Adaptive Intelligence"

def test_mixed_valid_and_malformed():
    events = [
        "Sep 05 10:01:12 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 ACTION=ALLOW",
        "CEF:0|VendorX|Firewall|1.0|100|Network Traffic|5|src=999.999.999.999 dst=10.0.0.10 act=ALLOW", # Invalid IP, will be quarantined
        '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","action":"DENY"}'
    ]
    response = client.post("/process/batch", json={"events": events})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["processed"] == 3
    results = data["results"]
    
    assert results[0]["validation"]["status"] == "VALID"
    assert results[1]["validation"]["status"] != "VALID" # Quarantined
    assert results[2]["validation"]["status"] == "VALID"

def test_raw_preservation():
    event = "random non sense log event"
    response = client.post("/process", json={"raw_payload": event})
    assert response.status_code == 200
    data = response.json()
    assert data["raw_event"] == event
