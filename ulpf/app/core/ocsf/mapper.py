from typing import Dict, Any, Tuple
from datetime import datetime
from app.models.universal_event import UniversalEvent
from app.core.ocsf.constants import (
    OCSF_VERSION,
    CLASS_NETWORK_ACTIVITY,
    CATEGORY_NETWORK_ACTIVITY,
    SEVERITY_MAP,
    ACTIVITY_MAP
)

def _map_severity(severity: str) -> Tuple[int, str]:
    if not severity:
        return 0, "Unknown"
    s = severity.lower()
    sev_id = SEVERITY_MAP.get(s, 99)
    return sev_id, severity.capitalize()

def _map_activity(action: str) -> Tuple[int, str]:
    if not action:
        return 0, "Unknown"
    act_lower = action.lower()
    act_id = ACTIVITY_MAP.get(act_lower, 99)
    return act_id, action.upper()

def map_to_ocsf(event: UniversalEvent, unmapped: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Maps UniversalEvent to OCSF v1.3.0 Network Activity class (4001).
    Preserves all endpoints, protocol, timestamp, activity, device, actor, and message details.
    """
    ocsf_event = {
        "metadata": {
            "version": OCSF_VERSION
        },
        "class_uid": CLASS_NETWORK_ACTIVITY,
        "class_name": "Network Activity",
        "category_uid": CATEGORY_NETWORK_ACTIVITY,
        "category_name": "Network Activity",
        "unmapped": {}
    }
    
    updated_unmapped = dict(unmapped)

    # 1. Source Endpoint
    if event.source:
        src_endpoint = {}
        if "ip" in event.source and event.source["ip"]:
            src_endpoint["ip"] = str(event.source["ip"])
        if "port" in event.source and event.source["port"] is not None:
            try:
                src_endpoint["port"] = int(event.source["port"])
            except (ValueError, TypeError):
                src_endpoint["port"] = event.source["port"]
        if "hostname" in event.source and event.source["hostname"]:
            src_endpoint["hostname"] = str(event.source["hostname"])
        if "domain" in event.source and event.source["domain"]:
            src_endpoint["domain"] = str(event.source["domain"])
            
        if src_endpoint:
            ocsf_event["src_endpoint"] = src_endpoint

        for k, v in event.source.items():
            if k not in ["ip", "port", "hostname", "domain"]:
                updated_unmapped[f"source.{k}"] = v

    # 2. Destination Endpoint
    if event.destination:
        dst_endpoint = {}
        if "ip" in event.destination and event.destination["ip"]:
            dst_endpoint["ip"] = str(event.destination["ip"])
        if "port" in event.destination and event.destination["port"] is not None:
            try:
                dst_endpoint["port"] = int(event.destination["port"])
            except (ValueError, TypeError):
                dst_endpoint["port"] = event.destination["port"]
        if "hostname" in event.destination and event.destination["hostname"]:
            dst_endpoint["hostname"] = str(event.destination["hostname"])
        if "domain" in event.destination and event.destination["domain"]:
            dst_endpoint["domain"] = str(event.destination["domain"])
            
        if dst_endpoint:
            ocsf_event["dst_endpoint"] = dst_endpoint

        for k, v in event.destination.items():
            if k not in ["ip", "port", "hostname", "domain"]:
                updated_unmapped[f"destination.{k}"] = v

    # 3. Connection Info / Network
    if event.network:
        proto_val = event.network.get("transport") or event.network.get("protocol")
        if proto_val:
            ocsf_event["connection_info"] = {
                "protocol_name": str(proto_val).lower()
            }
            
        for k, v in event.network.items():
            if k not in ["transport", "protocol"]:
                updated_unmapped[f"network.{k}"] = v

    # 4. Activity, Event Metadata, and Timestamps
    if event.event:
        if "action" in event.event and event.event["action"]:
            act_id, act_name = _map_activity(event.event["action"])
            ocsf_event["activity_id"] = act_id
            ocsf_event["activity_name"] = act_name
            ocsf_event["type_uid"] = CLASS_NETWORK_ACTIVITY * 100 + act_id
            ocsf_event["type_name"] = f"Network Activity: {act_name}"
            
        if "timestamp" in event.event and event.event["timestamp"]:
            ts_str = str(event.event["timestamp"])
            ocsf_event["time_dt"] = ts_str
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                ocsf_event["time"] = int(dt.timestamp() * 1000)
            except Exception:
                pass
            
        if "message" in event.event and event.event["message"]:
            ocsf_event["message"] = str(event.event["message"])
            
        for k, v in event.event.items():
            if k not in ["action", "timestamp", "message"]:
                updated_unmapped[f"event.{k}"] = v

    # 5. Severity
    if event.severity:
        sev_id, sev_name = _map_severity(event.severity)
        ocsf_event["severity_id"] = sev_id
        ocsf_event["severity"] = sev_name

    # 6. Device
    if event.device:
        if "hostname" in event.device and event.device["hostname"]:
            ocsf_event["device"] = {"hostname": str(event.device["hostname"])}
        for k, v in event.device.items():
            if k not in ["hostname"]:
                updated_unmapped[f"device.{k}"] = v
                
    # 7. User / Actor
    if event.user:
        if "name" in event.user and event.user["name"]:
            ocsf_event["actor"] = {"user": {"name": str(event.user["name"])}}
        for k, v in event.user.items():
            if k not in ["name"]:
                updated_unmapped[f"user.{k}"] = v

    return ocsf_event, updated_unmapped
