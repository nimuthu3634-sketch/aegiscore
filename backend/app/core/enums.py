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
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class ReportStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"


class IntegrationType(str, Enum):
    WAZUH = "wazuh"
    SURICATA = "suricata"
    NMAP = "nmap"
    HYDRA = "hydra"
