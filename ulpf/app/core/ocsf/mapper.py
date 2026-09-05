from typing import Dict, Any, Tuple
from app.models.universal_event import UniversalEvent
from app.core.ocsf.constants import (
    OCSF_VERSION,
    CLASS_NETWORK_ACTIVITY,
    CATEGORY_NETWORK_ACTIVITY,
    SEVERITY_MAP,
    ACTIVITY_MAP
)

def _map_severity(severity: str) -> Tuple[int, str]:
    """Map string severity to OCSF severity ID and string"""
    if not severity:
        return 0, "Unknown"
    
    s = severity.lower()
    sev_id = SEVERITY_MAP.get(s, 99)
    return sev_id, severity

def _map_activity(action: str) -> Tuple[int, str]:
    """Map string action to OCSF activity ID and string"""
    if not action:
        return 0, "Unknown"
        
    act_lower = action.lower()
    act_id = ACTIVITY_MAP.get(act_lower, 99)
    return act_id, action

def map_to_ocsf(event: UniversalEvent, unmapped: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Maps UniversalEvent to OCSF v1.3.0 Network Activity class.
    Fields that cannot be mapped remain in unmapped_fields.
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
    
    # Process unmapped fields to pass them through
    updated_unmapped = dict(unmapped)

    # 1. Source Endpoint
    if event.source:
        src_endpoint = {}
        if "ip" in event.source:
            src_endpoint["ip"] = event.source["ip"]
        if "port" in event.source:
            src_endpoint["port"] = event.source["port"]
        
        if src_endpoint:
            ocsf_event["src_endpoint"] = src_endpoint
            
        # Any other source fields? Pass through to unmapped or keep if it's ULPF unmapped
        for k, v in event.source.items():
            if k not in ["ip", "port"]:
                updated_unmapped[f"source.{k}"] = v

    # 2. Destination Endpoint
    if event.destination:
        dst_endpoint = {}
        if "ip" in event.destination:
            dst_endpoint["ip"] = event.destination["ip"]
        if "port" in event.destination:
            dst_endpoint["port"] = event.destination["port"]
            
        if dst_endpoint:
            ocsf_event["dst_endpoint"] = dst_endpoint
            
        for k, v in event.destination.items():
            if k not in ["ip", "port"]:
                updated_unmapped[f"destination.{k}"] = v

    # 3. Connection Info / Network
    if event.network:
        if "transport" in event.network:
            if "connection_info" not in ocsf_event:
                ocsf_event["connection_info"] = {}
            ocsf_event["connection_info"]["protocol_name"] = event.network["transport"]
            
        for k, v in event.network.items():
            if k not in ["transport"]:
                updated_unmapped[f"network.{k}"] = v

    # 4. Activity and Event metadata
    if event.event:
        if "action" in event.event:
            act_id, act_name = _map_activity(event.event["action"])
            ocsf_event["activity_id"] = act_id
            ocsf_event["activity_name"] = act_name
            
        if "timestamp" in event.event:
            # We map to time_dt (RFC3339 string)
            ocsf_event["time_dt"] = str(event.event["timestamp"])
            
        if "message" in event.event:
            ocsf_event["message"] = event.event["message"]
            
        for k, v in event.event.items():
            if k not in ["action", "timestamp", "message"]:
                updated_unmapped[f"event.{k}"] = v

    # 5. Severity
    if event.severity:
        sev_id, sev_name = _map_severity(event.severity)
        ocsf_event["severity_id"] = sev_id
        ocsf_event["severity"] = sev_name

    # 6. Device/User
    if event.device:
        if "hostname" in event.device:
            ocsf_event["device"] = {"hostname": event.device["hostname"]}
        for k, v in event.device.items():
            if k not in ["hostname"]:
                updated_unmapped[f"device.{k}"] = v
                
    if event.user:
        for k, v in event.user.items():
            updated_unmapped[f"user.{k}"] = v

    return ocsf_event, updated_unmapped
