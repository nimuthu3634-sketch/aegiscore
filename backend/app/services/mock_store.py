from datetime import datetime
from uuid import uuid4

from app.core.enums import (
    AlertSeverity,
    AlertStatus,
    IncidentStatus,
    IntegrationHealth,
    IntegrationTool,
    ReportStatus,
    ReportType,
    UserRole,
)
from app.core.security import get_password_hash
from app.utils.time import utc_now

DEMO_USERS: list[dict] = [
    {
        "id": "user-admin",
        "full_name": "AegisCore Admin",
        "email": "admin@aegiscore.local",
        "password_hash": get_password_hash("admin123"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "created_at": utc_now(),
    },
    {
        "id": "user-analyst",
        "full_name": "AegisCore Analyst",
        "email": "analyst@aegiscore.local",
        "password_hash": get_password_hash("analyst123"),
        "role": UserRole.ANALYST,
        "is_active": True,
        "created_at": utc_now(),
    },
]

DEMO_ALERTS: list[dict] = [
    {
        "id": "alert-001",
        "title": "Repeated SSH authentication failures",
        "description": "Wazuh detected repeated failed SSH attempts against a lab web host.",
        "source": "lab-web-01",
        "source_tool": "wazuh",
        "severity": AlertSeverity.HIGH,
        "status": AlertStatus.NEW,
        "confidence_score": 0.91,
        "created_at": utc_now(),
    },
    {
        "id": "alert-002",
        "title": "Unusual DNS request burst",
        "description": "Suricata observed DNS volume above the current classroom baseline.",
        "source": "sensor-east-02",
        "source_tool": "suricata",
        "severity": AlertSeverity.MEDIUM,
        "status": AlertStatus.TRIAGED,
        "confidence_score": 0.74,
        "created_at": utc_now(),
    },
]

DEMO_INCIDENTS: list[dict] = [
    {
        "id": "incident-001",
        "alert_id": "alert-001",
        "assigned_to_user_id": "user-analyst",
        "priority": AlertSeverity.HIGH,
        "status": IncidentStatus.IN_PROGRESS,
        "notes": "Validate the failed-login source and prepare an analyst handoff summary.",
        "opened_at": utc_now(),
        "closed_at": None,
    },
    {
        "id": "incident-002",
        "alert_id": "alert-002",
        "assigned_to_user_id": None,
        "priority": AlertSeverity.MEDIUM,
        "status": IncidentStatus.OPEN,
        "notes": "Awaiting analyst assignment for additional DNS traffic review.",
        "opened_at": utc_now(),
        "closed_at": None,
    },
]

DEMO_LOGS: list[dict] = [
    {
        "id": "log-001",
        "source": "lab-web-01",
        "source_tool": "wazuh",
        "raw_log": "Failed password for invalid user analyst from 10.0.0.22",
        "normalized_log": {"event": "failed_login", "username": "analyst", "source_ip": "10.0.0.22"},
        "event_type": "authentication",
        "severity": "high",
        "created_at": utc_now(),
    },
    {
        "id": "log-002",
        "source": "sensor-east-02",
        "source_tool": "suricata",
        "raw_log": "ET POLICY Suspicious DNS query burst observed.",
        "normalized_log": {"event": "dns_spike", "query_count": 240},
        "event_type": "network",
        "severity": "medium",
        "created_at": utc_now(),
    },
]

DEMO_REPORTS: list[dict] = [
    {
        "id": "report-001",
        "title": "Weekly SOC executive summary",
        "report_type": ReportType.EXECUTIVE,
        "generated_by_user_id": "user-admin",
        "content_json": {"alerts": 128, "incidents": 12, "summary": "Weekly overview placeholder"},
        "status": ReportStatus.READY,
        "created_at": utc_now(),
    },
    {
        "id": "report-002",
        "title": "Incident operations digest",
        "report_type": ReportType.INCIDENT,
        "generated_by_user_id": "user-analyst",
        "content_json": {"open_incidents": 7, "notes": "Operations report placeholder"},
        "status": ReportStatus.DRAFT,
        "created_at": utc_now(),
    },
]

DEMO_INTEGRATIONS: list[dict] = [
    {
        "id": "integration-001",
        "tool_name": IntegrationTool.WAZUH,
        "status": IntegrationHealth.CONNECTED,
        "last_sync_at": utc_now(),
        "notes": "Primary endpoint telemetry source.",
    },
    {
        "id": "integration-002",
        "tool_name": IntegrationTool.SURICATA,
        "status": IntegrationHealth.CONNECTED,
        "last_sync_at": utc_now(),
        "notes": "Primary network alert source.",
    },
    {
        "id": "integration-003",
        "tool_name": IntegrationTool.NMAP,
        "status": IntegrationHealth.PENDING,
        "last_sync_at": utc_now(),
        "notes": "Lab-only safe result ingestion placeholder.",
    },
]


def build_user_record(full_name: str, email: str, password_hash: str, role: UserRole) -> dict:
    return {
        "id": f"user-{uuid4()}",
        "full_name": full_name,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "is_active": True,
        "created_at": utc_now(),
    }
