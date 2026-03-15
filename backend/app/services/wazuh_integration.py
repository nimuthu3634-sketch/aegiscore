from app.core.enums import AlertSeverity, AlertStatus, IntegrationHealth, IntegrationTool
from app.services.alerts import create_alert
from app.services.integrations import get_augmented_integration_by_tool, get_integration_by_tool, get_latest_alert_titles_for_tool
from app.services.logs import create_log_record
from app.services.mock_store import DEMO_ALERTS, DEMO_LOGS
from app.utils.log_normalization import normalize_timestamp
from app.utils.time import utc_now


def _map_wazuh_level(level_value: int | str | float | None) -> AlertSeverity:
    try:
        numeric_level = float(level_value) if level_value is not None else 0
    except (TypeError, ValueError):
        numeric_level = 0

    if numeric_level >= 12:
        return AlertSeverity.CRITICAL
    if numeric_level >= 9:
        return AlertSeverity.HIGH
    if numeric_level >= 5:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _numeric_wazuh_level(level_value: int | str | float | None) -> float:
    try:
        return float(level_value) if level_value is not None else 0
    except (TypeError, ValueError):
        return 0


def _extract_event_type(alert_payload: dict) -> str:
    rule = alert_payload.get("rule", {})
    groups = [str(item).lower() for item in rule.get("groups", [])]
    description = str(rule.get("description", "")).lower()

    if any(keyword in groups for keyword in ("authentication_failed", "auth", "sshd", "windows")):
        return "authentication"
    if any(keyword in groups for keyword in ("malware", "virus", "trojan")):
        return "malware"
    if any(keyword in groups for keyword in ("network", "firewall", "suricata")):
        return "network"
    if any(keyword in description for keyword in ("sudo", "privilege", "root")):
        return "privilege_change"

    return "security_alert"


def _wazuh_reference(alert_payload: dict) -> str:
    payload_id = alert_payload.get("id")
    timestamp = alert_payload.get("timestamp") or alert_payload.get("@timestamp") or "unknown-time"
    rule = alert_payload.get("rule", {})
    rule_id = rule.get("id") or rule.get("description") or "unknown-rule"
    return f"wazuh:{payload_id or rule_id}:{timestamp}"


def _build_alert_description(alert_payload: dict) -> str:
    rule = alert_payload.get("rule", {})
    description = str(rule.get("description") or "Wazuh alert imported into AegisCore.")
    full_log = str(alert_payload.get("full_log") or alert_payload.get("message") or "").strip()

    if not full_log:
        return description

    return f"{description} Raw event: {full_log}"


def get_wazuh_status() -> dict:
    integration = get_augmented_integration_by_tool(IntegrationTool.WAZUH)
    latest_titles = get_latest_alert_titles_for_tool(IntegrationTool.WAZUH)

    return {
        **integration,
        "available_demo_payloads": 3,
        "latest_imported_alert_titles": latest_titles,
    }


def import_wazuh_alerts(alerts: list[dict]) -> dict:
    integration = get_integration_by_tool(IntegrationTool.WAZUH)
    imported_alert_count = 0
    imported_log_count = 0
    skipped_count = 0
    latest_titles: list[str] = []

    existing_references = {
        alert.get("integration_ref") for alert in DEMO_ALERTS if alert.get("integration_ref")
    }
    existing_references.update(
        log_entry.get("integration_ref") for log_entry in DEMO_LOGS if log_entry.get("integration_ref")
    )

    for alert_payload in alerts:
        integration_ref = _wazuh_reference(alert_payload)
        if integration_ref in existing_references:
            skipped_count += 1
            continue

        rule = alert_payload.get("rule", {})
        agent = alert_payload.get("agent", {})
        source = str(agent.get("name") or alert_payload.get("manager", {}).get("name") or "wazuh-agent")
        timestamp = normalize_timestamp(alert_payload.get("timestamp") or alert_payload.get("@timestamp"))
        level_value = _numeric_wazuh_level(rule.get("level"))
        severity = _map_wazuh_level(level_value)
        event_type = _extract_event_type(alert_payload)
        title = str(rule.get("description") or "Imported Wazuh alert")
        description = _build_alert_description(alert_payload)
        confidence_score = min(0.99, 0.45 + (level_value / 20))

        create_log_record(
            {
                "source": source,
                "source_tool": IntegrationTool.WAZUH,
                "timestamp": timestamp,
                "severity": severity.value,
                "event_type": event_type,
                "raw_log": alert_payload,
            },
            extra_fields={"integration_ref": integration_ref},
        )
        imported_log_count += 1

        create_alert(
            title=title,
            description=description,
            source=source,
            source_tool=IntegrationTool.WAZUH,
            severity=severity,
            status_value=AlertStatus.NEW,
            confidence_score=round(confidence_score, 2),
            created_at=timestamp,
            extra_fields={"integration_ref": integration_ref},
        )
        imported_alert_count += 1
        existing_references.add(integration_ref)
        latest_titles.append(title)

    last_import_at = utc_now()
    integration["status"] = IntegrationHealth.CONNECTED
    integration["last_sync_at"] = last_import_at
    integration["last_import_at"] = last_import_at
    integration["last_import_message"] = (
        f"Imported {imported_alert_count} Wazuh alerts and {imported_log_count} logs."
    )
    integration["notes"] = "Wazuh demo import ready for lab alert and log ingestion."

    return {
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "skipped_count": skipped_count,
        "last_import_at": last_import_at,
        "message": integration["last_import_message"],
        "latest_titles": latest_titles,
    }
