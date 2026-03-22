from app.core.enums import AlertSeverity, AlertStatus, IntegrationHealth, IntegrationTool
from app.services.alerts import create_alert
from app.services.integrations import (
    get_augmented_integration_by_tool,
    get_latest_alert_titles_for_tool,
    update_integration_runtime,
)
from app.services.logs import create_log_record, load_log_records
from app.utils.log_normalization import normalize_timestamp
from app.utils.time import utc_now


def _numeric_suricata_severity(level_value: int | str | float | None) -> float:
    try:
        return float(level_value) if level_value is not None else 3
    except (TypeError, ValueError):
        return 3


def _map_suricata_severity(level_value: int | str | float | None) -> AlertSeverity:
    numeric_level = _numeric_suricata_severity(level_value)
    if numeric_level <= 1:
        return AlertSeverity.CRITICAL
    if numeric_level <= 2:
        return AlertSeverity.HIGH
    if numeric_level <= 3:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _suricata_reference(event_payload: dict) -> str:
    timestamp = event_payload.get("timestamp") or "unknown-time"
    event_type = event_payload.get("event_type") or "event"
    alert = event_payload.get("alert", {})
    signature_id = alert.get("signature_id") or alert.get("gid") or "no-signature"
    src_ip = event_payload.get("src_ip") or "no-src"
    dest_ip = event_payload.get("dest_ip") or "no-dst"
    return f"suricata:{event_type}:{signature_id}:{timestamp}:{src_ip}:{dest_ip}"


def _extract_event_type(event_payload: dict) -> str:
    explicit_type = str(event_payload.get("event_type") or "").strip().lower()
    if explicit_type:
        return explicit_type.replace(" ", "_")

    alert = event_payload.get("alert", {})
    category = str(alert.get("category") or "").lower()
    if "dns" in category:
        return "dns_alert"
    if "malware" in category:
        return "malware"
    if "scan" in category or "recon" in category:
        return "reconnaissance"
    return "network"


def _build_alert_title(event_payload: dict) -> str:
    alert = event_payload.get("alert", {})
    return str(alert.get("signature") or "Imported Suricata network alert")


def _build_alert_description(event_payload: dict) -> str:
    alert = event_payload.get("alert", {})
    category = alert.get("category")
    src_ip = event_payload.get("src_ip")
    dest_ip = event_payload.get("dest_ip")
    proto = event_payload.get("proto")
    message = str(alert.get("signature") or event_payload.get("message") or "Imported Suricata event.")

    details: list[str] = [message]
    if category:
        details.append(f"Category: {category}.")
    if src_ip and dest_ip:
        details.append(f"Flow: {src_ip} -> {dest_ip}.")
    if proto:
        details.append(f"Protocol: {proto}.")

    return " ".join(details)


def _build_source(event_payload: dict) -> str:
    return str(
        event_payload.get("sensor_name")
        or event_payload.get("host")
        or event_payload.get("src_ip")
        or "suricata-sensor"
    )


def get_suricata_status() -> dict:
    integration = get_augmented_integration_by_tool(IntegrationTool.SURICATA)
    latest_titles = get_latest_alert_titles_for_tool(IntegrationTool.SURICATA)

    return {
        **integration,
        "available_demo_payloads": 3,
        "latest_imported_alert_titles": latest_titles,
    }


def import_suricata_events(events: list[dict]) -> dict:
    imported_alert_count = 0
    imported_log_count = 0
    skipped_count = 0

    existing_references = set()
    for log_entry in load_log_records():
        if log_entry.get("source_tool") != IntegrationTool.SURICATA:
            continue

        if log_entry.get("integration_ref"):
            existing_references.add(log_entry["integration_ref"])

        raw_log = log_entry.get("raw_log")
        if isinstance(raw_log, dict):
            existing_references.add(_suricata_reference(raw_log))

    for event_payload in events:
        integration_ref = _suricata_reference(event_payload)
        if integration_ref in existing_references:
            skipped_count += 1
            continue

        timestamp = normalize_timestamp(event_payload.get("timestamp"))
        event_type = _extract_event_type(event_payload)
        alert_data = event_payload.get("alert", {})
        source = _build_source(event_payload)
        severity = _map_suricata_severity(alert_data.get("severity"))
        finding_metadata = {
            "event_type": event_type,
            "source_ip": event_payload.get("src_ip"),
            "destination_ip": event_payload.get("dest_ip"),
            "signature": alert_data.get("signature"),
            "category": alert_data.get("category"),
        }

        create_log_record(
            {
                "source": source,
                "source_tool": IntegrationTool.SURICATA,
                "timestamp": timestamp,
                "severity": severity.value,
                "event_type": event_type,
                "raw_log": event_payload,
            },
            extra_fields={
                "integration_ref": integration_ref,
                "finding_metadata": finding_metadata,
                "parser_status": "normalized",
            },
        )
        imported_log_count += 1

        if event_type == "alert" or alert_data:
            confidence_score = min(0.98, 0.5 + (4 - _numeric_suricata_severity(alert_data.get("severity"))) * 0.12)
            create_alert(
                title=_build_alert_title(event_payload),
                description=_build_alert_description(event_payload),
                source=source,
                source_tool=IntegrationTool.SURICATA,
                severity=severity,
                status_value=AlertStatus.NEW,
                confidence_score=round(confidence_score, 2),
                created_at=timestamp,
                extra_fields={
                    "integration_ref": integration_ref,
                    "finding_metadata": finding_metadata,
                    "parser_status": "normalized",
                },
            )
            imported_alert_count += 1

        existing_references.add(integration_ref)

    last_import_at = utc_now()
    last_import_message = (
        f"Imported {imported_alert_count} Suricata alerts and {imported_log_count} logs."
    )
    update_integration_runtime(
        IntegrationTool.SURICATA,
        status=IntegrationHealth.CONNECTED,
        last_sync_at=last_import_at,
        last_import_at=last_import_at,
        last_import_message=last_import_message,
        notes="Suricata import ready for network threat review.",
    )

    return {
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "skipped_count": skipped_count,
        "last_import_at": last_import_at,
        "message": last_import_message,
    }
