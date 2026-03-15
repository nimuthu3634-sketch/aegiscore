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


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    READY = "ready"


class ReportType(str, Enum):
    EXECUTIVE = "executive"
    INCIDENT = "incident"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"


class IntegrationTool(str, Enum):
    WAZUH = "wazuh"
    SURICATA = "suricata"
    NMAP = "nmap"
    HYDRA = "hydra"
    VIRTUALBOX = "virtualbox"


class IntegrationHealth(str, Enum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    PENDING = "pending"
    OFFLINE = "offline"


class VirtualMachineStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    PAUSED = "paused"
    PROVISIONING = "provisioning"
