from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(str, Enum):
    NEW = "new"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class ResponseActionType(str, Enum):
    CREATE_INCIDENT = "create_incident"
    BLOCK_SOURCE_IP = "block_source_ip"
    ISOLATE_ASSET = "isolate_asset"
    DISABLE_ACCOUNT = "disable_account"
    MARK_INVESTIGATING = "mark_investigating"


class ResponseActionStatus(str, Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ResponseActionMode(str, Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IntegrationTool(str, Enum):
    WAZUH = "wazuh"
    SURICATA = "suricata"
    NMAP = "nmap"
    HYDRA = "hydra"
    LANL = "lanl"
    VIRTUALBOX = "virtualbox"


class IntegrationHealth(str, Enum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    PENDING = "pending"
    OFFLINE = "offline"


SUPPORTED_INTEGRATION_TOOL_VALUES = {
    IntegrationTool.WAZUH.value,
    IntegrationTool.SURICATA.value,
    IntegrationTool.NMAP.value,
    IntegrationTool.HYDRA.value,
}
