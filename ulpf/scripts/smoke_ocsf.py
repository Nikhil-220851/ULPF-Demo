import requests, json

BASE = 'http://127.0.0.1:8010'

tests = [
    ('SYSLOG', 'Sep 05 09:15:22 firewall01 SRCIP=192.168.10.25 DSTIP=10.0.0.5 SRCPORT=443 DSTPORT=52144 PROTO=TCP ACTION=ALLOW SEVERITY=5'),
    ('CEF',    'CEF:0|PaloAlto|Firewall|11.0|1001|Network Traffic|5|src=192.168.1.30 dst=10.0.0.10 spt=8080 dpt=443 proto=TCP act=ALLOW'),
    ('JSON',   '{"source_ip":"192.168.1.20","destination_ip":"10.0.0.8","source_port":22,"destination_port":443,"protocol":"TCP","action":"DENY"}'),
]

all_ok = True
for name, payload in tests:
    r = requests.post(f'{BASE}/process', json={'raw_payload': payload})
    d = r.json()
    o = d.get('ocsf') or {}
    v = d.get('ocsf_validation') or {}
    ok = bool(o) and v.get('status') == 'VALID'
    all_ok = all_ok and ok
    print(f"[{'OK' if ok else 'FAIL'}] {name}")
    print(f"  format:          {d.get('detected_format')}")
    print(f"  ocsf.class_uid:  {o.get('class_uid')}")
    print(f"  ocsf.src_ip:     {o.get('src_endpoint', {}).get('ip')}")
    print(f"  ocsf.dst_ip:     {o.get('dst_endpoint', {}).get('ip')}")
    print(f"  ocsf.activity:   {o.get('activity_id')} ({o.get('activity_name')})")
    print(f"  ocsf_valid:      {v.get('status')}")
    print()

print('ALL PASS' if all_ok else 'SOME FAILED')
