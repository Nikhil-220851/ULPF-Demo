import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(name, payload):
    print(f"\n--- Testing {name} ---")
    try:
        response = requests.post(f"{BASE_URL}/process", json={"raw_payload": payload})
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def run_tests():
    try:
        health = requests.get(f"{BASE_URL}/health")
        print("Health:", health.json())
    except Exception as e:
        print("Backend offline!", e)
        sys.exit(1)
        
    tests = [
        ("CEF", "CEF:0|VendorX|Firewall|1.0|100|Network Connection|5|src=192.168.1.10 dst=10.0.0.5 spt=443 act=ALLOW"),
        ("JSON", '{"source_ip": "192.168.1.20", "destination_ip": "10.0.0.8", "source_port": 22, "action": "DENY"}'),
        ("Syslog", "Sep 04 10:32:15 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 SRCPORT=443 ACTION=ALLOW"),
        ("Unknown", "192.168.1.40 | 10.0.0.20 | 443 | DENY"),
        ("Malformed / Invalid IP", "src=999.999.1.10 dst=10.0.0.5 act=ALLOW")
    ]
    
    all_passed = True
    for name, payload in tests:
        if not test_endpoint(name, payload):
            all_passed = False
            
    if all_passed:
        print("\nALL BACKEND TESTS PASSED.")
    else:
        print("\nSOME TESTS FAILED.")

if __name__ == "__main__":
    run_tests()
