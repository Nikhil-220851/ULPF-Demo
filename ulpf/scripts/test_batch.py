import requests

# Health
r = requests.get('http://127.0.0.1:8000/health')
print('Health:', r.json())

# --- Test 1: 3-line syslog batch ---
events = [
    'Sep 05 09:15:22 firewall01 SRCIP=192.168.10.25 DSTIP=10.20.30.40 SRCPORT=52341 ACTION=ALLOW SEVERITY=5',
    'Sep 05 09:16:03 firewall01 SRCIP=192.168.10.26 DSTIP=10.20.30.50 SRCPORT=53122 ACTION=DENY SEVERITY=7',
    'Sep 05 09:17:45 firewall01 SRCIP=172.16.1.15 DSTIP=10.20.30.60 SRCPORT=49821 ACTION=ALLOW SEVERITY=4',
]
r = requests.post('http://127.0.0.1:8000/process/batch', json={'events': events})
d = r.json()
print(f'\n[Test 1] 3-line syslog batch: status={r.status_code} total={d["total"]} processed={d["processed"]}')
for i, res in enumerate(d['results']):
    fmt = res['detected_format']
    val = res['validation']['status']
    raw = res['raw_event'][:50]
    print(f'  Event {i+1}: format={fmt} validation={val} raw={raw}')
assert d['total'] == 3 and d['processed'] == 3, 'FAIL: not all events processed'
print('Test 1: PASS')

# --- Test 2: Mixed (known + unknown + malformed) ---
mixed = [
    'Sep 05 10:01:12 firewall01 SRCIP=192.168.1.10 DSTIP=10.0.0.5 SRCPORT=443 DSTPORT=52144 PROTO=TCP ACTION=ALLOW SEVERITY=5',
    '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","source_port":22,"destination_port":443,"protocol":"TCP","action":"DENY"}',
    'CEF:0|PaloAlto|Firewall|11.0|1001|Network Traffic|5|src=192.168.1.30 dst=10.0.0.10 spt=8080 dpt=443 proto=TCP act=ALLOW',
    '172.16.50.21|10.10.20.15|54321|443|BLOCK|TCP',
    'Sep 05 10:04:51 firewall02 SRCIP=10.1.1.15 DSTIP=192.168.10.20 SRCPORT=3389 DSTPORT=49152 PROTO=TCP ACTION=DENY SEVERITY=8',
    '{"source_ip":"10.2.2.10","destination_ip":"172.16.1.50","source_port":53,"destination_port":53000,"protocol":"UDP","action":"ALLOW"}',
]
r2 = requests.post('http://127.0.0.1:8000/process/batch', json={'events': mixed})
d2 = r2.json()
print(f'\n[Test 2] Mixed 6-event batch: status={r2.status_code} total={d2["total"]} processed={d2["processed"]}')
for i, res in enumerate(d2['results']):
    fmt = res['detected_format']
    parser = res.get('parser', 'None')
    val = res['validation']['status']
    raw = res['raw_event'][:50]
    print(f'  Event {i+1}: format={fmt} parser={parser} validation={val} raw={raw}')
assert d2['total'] == 6 and d2['processed'] == 6, 'FAIL'

# Verify formats exactly
expected_formats = ['SYSLOG', 'JSON', 'CEF', 'UNKNOWN', 'SYSLOG', 'JSON']
actual_formats = [res['detected_format'] for res in d2['results']]
assert actual_formats == expected_formats, f'FAIL: expected {expected_formats} but got {actual_formats}'
print('Test 2: PASS')

# --- Test 3: JSON events ---
json_events = [
    '{"source_ip": "192.168.1.20", "destination_ip": "10.0.0.8", "source_port": 22, "action": "DENY"}',
    '{"source_ip": "192.168.1.21", "destination_ip": "10.0.0.9", "source_port": 443, "action": "ALLOW"}',
]
r3 = requests.post('http://127.0.0.1:8000/process/batch', json={'events': json_events})
d3 = r3.json()
print(f'\n[Test 3] JSON batch: status={r3.status_code} total={d3["total"]} processed={d3["processed"]}')
for i, res in enumerate(d3['results']):
    print(f'  Event {i+1}: format={res["detected_format"]} validation={res["validation"]["status"]}')
assert d3['total'] == 2 and d3['processed'] == 2, 'FAIL'
print('Test 3: PASS')

# --- Test 4: Single event still works ---
r4 = requests.post('http://127.0.0.1:8000/process', json={'raw_payload': 'CEF:0|VendorX|Firewall|1.0|100|Conn|5|src=192.168.1.30 dst=10.0.0.10 act=ALLOW'})
d4 = r4.json()
print(f'\n[Test 4] Single event: status={r4.status_code} format={d4["detected_format"]} validation={d4["validation"]["status"]}')
assert d4['detected_format'] == 'CEF', 'FAIL'
print('Test 4: PASS')

print('\nALL BATCH TESTS PASSED.')
