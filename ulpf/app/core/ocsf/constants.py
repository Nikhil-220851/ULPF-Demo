# OCSF Constants and Configuration

OCSF_VERSION = "1.3.0"

# Class Constants
CLASS_NETWORK_ACTIVITY = 4001
CATEGORY_NETWORK_ACTIVITY = 4

# Field Type Constants
TYPE_IP = "ip"
TYPE_PORT = "port"
TYPE_STRING = "string"
TYPE_INTEGER = "integer"

# Severity mapping ULPF -> OCSF Severity ID
SEVERITY_MAP = {
    "unknown": 0,
    "informational": 1,
    "low": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
    "fatal": 6,
    "other": 99
}

# Activity mapping ULPF -> OCSF Activity ID
ACTIVITY_MAP = {
    "unknown": 0,
    "allow": 1,
    "deny": 2,
    "drop": 3,
    "reject": 3,
    "block": 3,
    "timeout": 4,
    "reset": 5,
    "other": 99
}
