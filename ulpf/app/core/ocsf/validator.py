from typing import Dict, Any, Tuple
import re

# Basic IP validation (IPv4 and IPv6)
IPV4_REGEX = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
IPV6_REGEX = re.compile(r"^(?:[A-F0-9]{1,4}:){7}[A-F0-9]{1,4}$", re.IGNORECASE)

def _is_valid_ip(ip: str) -> bool:
    if not isinstance(ip, str):
        return False
    return bool(IPV4_REGEX.match(ip) or IPV6_REGEX.match(ip))

def _is_valid_port(port: Any) -> bool:
    try:
        p = int(port)
        return 0 <= p <= 65535
    except (ValueError, TypeError):
        return False

def validate_ocsf(ocsf_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates an OCSF event to ensure it meets standard requirements.
    """
    errors = []
    warnings = []
    
    # 1. Check Class and Category
    if "class_uid" not in ocsf_event:
        errors.append("Missing required field: class_uid")
    elif ocsf_event["class_uid"] != 4001:
        errors.append(f"Invalid class_uid for Network Activity: {ocsf_event['class_uid']}")
        
    if "category_uid" not in ocsf_event:
        errors.append("Missing required field: category_uid")
    elif ocsf_event["category_uid"] != 4:
        errors.append(f"Invalid category_uid for Network Activity: {ocsf_event['category_uid']}")

    # 2. Check src_endpoint
    if "src_endpoint" in ocsf_event:
        src = ocsf_event["src_endpoint"]
        if "ip" in src and not _is_valid_ip(src["ip"]):
            errors.append(f"Invalid source IP format: {src['ip']}")
        if "port" in src and not _is_valid_port(src["port"]):
            errors.append(f"Invalid source port format: {src['port']}")
            
    # 3. Check dst_endpoint
    if "dst_endpoint" in ocsf_event:
        dst = ocsf_event["dst_endpoint"]
        if "ip" in dst and not _is_valid_ip(dst["ip"]):
            errors.append(f"Invalid destination IP format: {dst['ip']}")
        if "port" in dst and not _is_valid_port(dst["port"]):
            errors.append(f"Invalid destination port format: {dst['port']}")
            
    # 4. Connection info
    if "connection_info" in ocsf_event:
        conn = ocsf_event["connection_info"]
        if "protocol_name" in conn and not isinstance(conn["protocol_name"], str):
            errors.append("protocol_name must be a string")

    # 5. Metadata version
    if "metadata" in ocsf_event and "version" in ocsf_event["metadata"]:
        if not isinstance(ocsf_event["metadata"]["version"], str):
            errors.append("metadata.version must be a string")

    status = "VALID" if not errors else "INVALID"
    
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings
    }
