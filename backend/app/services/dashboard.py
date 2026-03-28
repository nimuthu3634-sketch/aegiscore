from collections import Counter
from datetime import datetime, timedelta

from app.core.enums import AlertSeverity, IncidentStatus
from app.services.anomaly import ensure_demo_alerts_scored
from app.services.alerts import load_alert_records
from app.services.incidents import load_incident_records
from app.services.users import get_user_name_lookup

SEVERITY_ORDER = [
    AlertSeverity.CRITICAL,
    AlertSeverity.HIGH,
    AlertSeverity.MEDIUM,
    AlertSeverity.LOW,
]

SOURCE_TOOL_ORDER = ["wazuh", "suricata", "nmap", "hydra"]


def _incident_updated_at(incident: dict) -> datetime:
    return incident.get("updated_at") or incident.get("closed_at") or incident["opened_at"]


def _sorted_alerts() -> list[dict]:
    ensure_demo_alerts_scored()
    return sorted(load_alert_records(), key=lambda alert: alert["created_at"], reverse=True)


def _sorted_incidents() -> list[dict]:
    return sorted(load_incident_records(), key=_incident_updated_at, reverse=True)


def get_dashboard_summary() -> dict:
    alert_records = load_alert_records()
    incident_records = load_incident_records()
    total_alerts = len(alert_records)
    critical_alerts = sum(1 for alert in alert_records if alert["severity"] == AlertSeverity.CRITICAL)
    resolved_incidents = sum(
        1 for incident in incident_records if incident["status"] == IncidentStatus.RESOLVED
    )

    return {
        "total_alerts": total_alerts,
        "critical_alerts": critical_alerts,
        "open_incidents": len(incident_records) - resolved_incidents,
        "resolved_incidents": resolved_incidents,
    }


def get_dashboard_charts() -> dict:
    alert_records = load_alert_records()
    latest_alert_day = max(alert["created_at"].date() for alert in alert_records)
    daily_counts = Counter(alert["created_at"].date() for alert in alert_records)
    severity_counts = Counter(alert["severity"] for alert in alert_records)
    source_tool_counts = Counter(alert["source_tool"] for alert in alert_records)

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
    user_lookup = get_user_name_lookup()
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
    ensure_demo_alerts_scored()
    from app.ml.anomaly import anomaly_detector

    alert_records = _sorted_alerts()
    metadata = anomaly_detector.get_training_metadata()
    anomaly_scores = [float(alert.get("anomaly_score", 0.0)) for alert in alert_records]
    top_anomalous_alerts = sorted(
        alert_records,
        key=lambda alert: (float(alert.get("anomaly_score", 0.0)), alert.get("created_at")),
        reverse=True,
    )[:5]

    summary = {
        "model_name": metadata.model_name,
        "trained_on_events": metadata.trained_on_events,
        "feature_labels": metadata.feature_labels,
        "trained_at": metadata.trained_at,
        "average_anomaly_score": round(sum(anomaly_scores) / len(anomaly_scores), 2)
        if anomaly_scores
        else 0.0,
        "anomalous_alert_count": sum(1 for alert in alert_records if alert.get("is_anomalous")),
        "high_anomaly_alert_count": sum(
            1 for alert in alert_records if float(alert.get("anomaly_score", 0.0)) >= 0.7
        ),
        "top_anomalous_alerts": top_anomalous_alerts,
    }
    return {
        **summary,
        "top_anomalous_alerts": summary["top_anomalous_alerts"],
    }
