from app.core.enums import AlertSeverity, AlertStatus, IntegrationHealth, IntegrationTool
from app.services.alerts import create_alert
from app.services.integrations import (
    get_augmented_integration_by_tool,
    get_integration_by_tool,
    get_latest_alert_titles_for_tool,
)
from app.services.logs import create_log_record, load_log_records
from app.utils.log_normalization import normalize_timestamp
from app.utils.time import utc_now

RISKY_PORTS = {23, 445, 3389, 5900, 5985, 5986}
EXPOSED_DATA_PORTS = {3306, 5432, 6379, 9200}
RISKY_SERVICES = {
    "ftp",
    "mssql",
    "mysql",
    "netbios-ssn",
    "postgres",
    "postgresql",
    "redis",
    "rdp",
    "smb",
    "telnet",
    "vnc",
    "winrm",
}


def _build_nmap_reference(result_payload: dict) -> str:
    host = str(result_payload.get("host") or "unknown-host")
    timestamp = result_payload.get("scan_timestamp") or "unknown-time"
    port_fingerprint = "-".join(
        str(port_record.get("port") or "unknown-port") for port_record in result_payload.get("open_ports", [])
    )
    return f"nmap:{host}:{timestamp}:{port_fingerprint or 'no-open-ports'}"


def _normalized_ports(result_payload: dict) -> list[dict]:
    normalized_ports: list[dict] = []

    for port_record in result_payload.get("open_ports", []):
        if isinstance(port_record, int):
            normalized_ports.append(
                {
                    "port": port_record,
                    "service_name": "unknown",
                    "protocol": "tcp",
                    "state": "open",
                }
            )
            continue

        if not isinstance(port_record, dict):
            continue

        port_value = port_record.get("port")
        try:
            normalized_port = int(port_value)
        except (TypeError, ValueError):
            continue

        normalized_ports.append(
            {
                "port": normalized_port,
                "service_name": str(port_record.get("service_name") or port_record.get("service") or "unknown"),
                "protocol": str(port_record.get("protocol") or "tcp"),
                "state": str(port_record.get("state") or "open"),
            }
        )

    return normalized_ports


def _service_names(result_payload: dict, open_ports: list[dict]) -> list[str]:
    explicit_names = [str(item).strip() for item in result_payload.get("service_names", []) if str(item).strip()]
    if explicit_names:
        return sorted(set(explicit_names))

    return sorted(
        {
            str(port_record["service_name"]).strip()
            for port_record in open_ports
            if str(port_record.get("service_name") or "").strip() and port_record["service_name"] != "unknown"
        }
    )


def _map_nmap_severity(open_ports: list[dict], service_names: list[str]) -> AlertSeverity:
    port_numbers = {int(port_record["port"]) for port_record in open_ports}
    normalized_services = {service_name.lower() for service_name in service_names}

    if port_numbers & RISKY_PORTS:
        return AlertSeverity.CRITICAL

    if port_numbers & EXPOSED_DATA_PORTS or normalized_services & RISKY_SERVICES:
        return AlertSeverity.HIGH

    if len(open_ports) >= 4:
        return AlertSeverity.MEDIUM

    return AlertSeverity.LOW


def _build_nmap_title(host: str, open_ports: list[dict]) -> str:
    if not open_ports:
        return f"Authorized Nmap result imported for {host}"

    top_port_labels = ", ".join(
        f"{port_record['protocol']}/{port_record['port']}" for port_record in open_ports[:3]
    )
    return f"Authorized Nmap result: {host} exposes {top_port_labels}"


def _build_nmap_description(host: str, open_ports: list[dict], service_names: list[str], notes: str | None) -> str:
    port_details = ", ".join(
        f"{port_record['protocol']}/{port_record['port']} ({port_record['service_name']})"
        for port_record in open_ports
    )
    service_details = ", ".join(service_names) if service_names else "No service names supplied"

    details = [
        f"Authorized Nmap result ingestion for {host}.",
        f"Open ports: {port_details or 'none reported'}.",
        f"Services: {service_details}.",
    ]

    if notes:
        details.append(f"Notes: {notes.strip()}.")

    details.append("AegisCore stores imported findings only and does not execute scans or automation.")
    return " ".join(details)


def _build_nmap_message(host: str, open_ports: list[dict]) -> str:
    if not open_ports:
        return f"Authorized Nmap result import for {host} recorded no open ports."

    return (
        f"Authorized Nmap result import for {host} identified "
        f"{len(open_ports)} open ports for validation."
    )


def _confidence_score(open_ports: list[dict], severity: AlertSeverity) -> float:
    base_scores = {
        AlertSeverity.CRITICAL: 0.91,
        AlertSeverity.HIGH: 0.84,
        AlertSeverity.MEDIUM: 0.76,
        AlertSeverity.LOW: 0.64,
    }
    return min(0.98, base_scores[severity] + min(len(open_ports), 4) * 0.02)


def get_nmap_status() -> dict:
    integration = get_augmented_integration_by_tool(IntegrationTool.NMAP)
    latest_titles = get_latest_alert_titles_for_tool(IntegrationTool.NMAP)

    return {
        **integration,
        "available_demo_payloads": 3,
        "latest_imported_alert_titles": latest_titles,
    }


def import_nmap_results(results: list[dict]) -> dict:
    integration = get_integration_by_tool(IntegrationTool.NMAP)
    imported_alert_count = 0
    imported_log_count = 0
    skipped_count = 0

    existing_references = set()
    for log_entry in load_log_records():
        if log_entry.get("source_tool") != IntegrationTool.NMAP:
            continue

        if log_entry.get("integration_ref"):
            existing_references.add(log_entry["integration_ref"])

        raw_log = log_entry.get("raw_log")
        if isinstance(raw_log, dict):
            reference_payload = {
                "host": raw_log.get("host"),
                "scan_timestamp": raw_log.get("timestamp"),
                "open_ports": raw_log.get("open_ports", []),
            }
            existing_references.add(_build_nmap_reference(reference_payload))

    for result_payload in results:
        integration_ref = _build_nmap_reference(result_payload)
        if integration_ref in existing_references:
            skipped_count += 1
            continue

        host = str(result_payload.get("host") or "unknown-lab-host")
        timestamp = normalize_timestamp(result_payload.get("scan_timestamp"))
        open_ports = _normalized_ports(result_payload)
        service_names = _service_names(result_payload, open_ports)
        severity = _map_nmap_severity(open_ports, service_names)
        scan_notes = str(result_payload.get("scan_notes") or "").strip() or None
        title = _build_nmap_title(host, open_ports)
        description = _build_nmap_description(host, open_ports, service_names, scan_notes)
        message = _build_nmap_message(host, open_ports)
        finding_metadata = {
            "host": host,
            "open_ports": open_ports,
            "service_names": service_names,
            "assessment_scope": "authorized_lab_only_result_ingestion",
            "usage_boundary": "no_offensive_automation",
        }

        raw_log = {
            "host": host,
            "timestamp": timestamp.isoformat(),
            "open_ports": open_ports,
            "service_names": service_names,
            "scan_notes": scan_notes,
            "message": message,
            "assessment_scope": "Authorized assessment result ingestion",
            "usage_boundary": "No offensive automation",
        }

        create_log_record(
            {
                "source": host,
                "source_tool": IntegrationTool.NMAP,
                "timestamp": timestamp,
                "severity": severity.value,
                "event_type": "scan_result",
                "raw_log": raw_log,
            },
            extra_fields={"integration_ref": integration_ref, "finding_metadata": finding_metadata},
        )
        imported_log_count += 1

        create_alert(
            title=title,
            description=description,
            source=host,
            source_tool=IntegrationTool.NMAP,
            severity=severity,
            status_value=AlertStatus.NEW,
            confidence_score=round(_confidence_score(open_ports, severity), 2),
            created_at=timestamp,
            extra_fields={"integration_ref": integration_ref, "finding_metadata": finding_metadata},
        )
        imported_alert_count += 1
        existing_references.add(integration_ref)

    last_import_at = utc_now()
    integration["status"] = IntegrationHealth.CONNECTED
    integration["last_sync_at"] = last_import_at
    integration["last_import_at"] = last_import_at
    integration["last_import_message"] = (
        f"Imported {imported_alert_count} Nmap findings and {imported_log_count} logs."
    )
    integration["notes"] = "Authorized assessment result ingestion for scan findings. No offensive automation."

    return {
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "skipped_count": skipped_count,
        "last_import_at": last_import_at,
        "message": integration["last_import_message"],
    }
