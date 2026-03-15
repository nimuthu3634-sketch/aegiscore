from collections import Counter
from datetime import datetime, timedelta

from app.core.enums import AlertSeverity, IncidentStatus
from app.services.anomaly import ensure_demo_alerts_scored, get_anomaly_summary
from app.services.mock_store import DEMO_ALERTS, DEMO_INCIDENTS, DEMO_USERS

SEVERITY_ORDER = [
    AlertSeverity.CRITICAL,
    AlertSeverity.HIGH,
    AlertSeverity.MEDIUM,
    AlertSeverity.LOW,
]

SOURCE_TOOL_ORDER = ["wazuh", "suricata", "nmap", "hydra", "virtualbox"]


def _incident_updated_at(incident: dict) -> datetime:
    return incident.get("updated_at") or incident.get("closed_at") or incident["opened_at"]


def _sorted_alerts() -> list[dict]:
    ensure_demo_alerts_scored()
    return sorted(DEMO_ALERTS, key=lambda alert: alert["created_at"], reverse=True)


def _sorted_incidents() -> list[dict]:
    return sorted(DEMO_INCIDENTS, key=_incident_updated_at, reverse=True)


def get_dashboard_summary() -> dict:
    total_alerts = len(DEMO_ALERTS)
    critical_alerts = sum(1 for alert in DEMO_ALERTS if alert["severity"] == AlertSeverity.CRITICAL)
    resolved_incidents = sum(
        1 for incident in DEMO_INCIDENTS if incident["status"] == IncidentStatus.RESOLVED
    )

    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "open_incidents": len(DEMO_INCIDENTS) - resolved_incidents,
        "resolved_incidents": resolved_incidents,
    }


def get_dashboard_charts() -> dict:
    latest_alert_day = max(alert["created_at"].date() for alert in DEMO_ALERTS)
    daily_counts = Counter(alert["created_at"].date() for alert in DEMO_ALERTS)
    severity_counts = Counter(alert["severity"] for alert in DEMO_ALERTS)
    source_tool_counts = Counter(alert["source_tool"] for alert in DEMO_ALERTS)

    alerts_over_time = []
    for offset in range(6, -1, -1):
        day = latest_alert_day - timedelta(days=offset)
        alerts_over_time.append({"label": day.strftime("%a"), "total": daily_counts.get(day, 0)})

    alerts_by_severity = [
        {"severity": severity, "count": severity_counts.get(severity, 0)}
        for severity in SEVERITY_ORDER
    ]

    alerts_by_source_tool = [
        {"source_tool": source_tool, "count": source_tool_counts.get(source_tool, 0)}
        for source_tool in SOURCE_TOOL_ORDER
    ]

    return {
        "alerts_over_time": alerts_over_time,
        "alerts_by_severity": alerts_by_severity,
        "alerts_by_source_tool": alerts_by_source_tool,
    }


def get_dashboard_recent_alerts(limit: int = 5) -> list[dict]:
    return _sorted_alerts()[:limit]


def get_dashboard_recent_incidents(limit: int = 4) -> list[dict]:
    user_lookup = {user["id"]: user["full_name"] for user in DEMO_USERS}
    recent_incidents: list[dict] = []

    for incident in _sorted_incidents()[:limit]:
        recent_incidents.append(
            {
                "id": incident["id"],
                "title": incident.get("title") or "Incident review",
                "priority": incident["priority"],
                "status": incident["status"],
                "analyst_name": user_lookup.get(incident.get("assigned_to_user_id")),
                "affected_asset": incident.get("affected_asset") or "Unknown asset",
                "summary": incident.get("summary") or incident["notes"],
                "updated_at": _incident_updated_at(incident),
            }
        )

    return recent_incidents


def get_dashboard_anomaly_summary() -> dict:
    summary = get_anomaly_summary(limit=5)
    return {
        **summary,
        "top_anomalous_alerts": summary["top_anomalous_alerts"],
    }
