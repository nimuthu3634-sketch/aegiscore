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


def _build_hydra_reference(result_payload: dict) -> str:
    target_system = str(result_payload.get("target_system") or result_payload.get("target") or "unknown-target")
    protocol = str(result_payload.get("protocol") or "unknown-protocol")
    timestamp = result_payload.get("timestamp") or "unknown-time"
    summary = str(result_payload.get("result_summary") or "no-summary").strip().lower().replace(" ", "-")
    return f"hydra:{target_system}:{protocol}:{timestamp}:{summary[:48]}"


def _map_hydra_severity(summary: str, notes: str | None) -> AlertSeverity:
    combined_text = f"{summary} {notes or ''}".lower()

    if any(keyword in combined_text for keyword in ("valid credential", "valid login", "successful login", "credential match")):
        return AlertSeverity.CRITICAL

    if any(keyword in combined_text for keyword in ("threshold", "repeated match", "multiple match", "lockout", "password reuse")):
        return AlertSeverity.HIGH

    if any(keyword in combined_text for keyword in ("failed attempt", "failed login", "retry", "assessment")):
        return AlertSeverity.MEDIUM

    return AlertSeverity.LOW


def _build_hydra_title(target_system: str, protocol: str) -> str:
    return f"Authorized Hydra result imported for {target_system} ({protocol})"


def _build_hydra_description(
    target_system: str,
    protocol: str,
    result_summary: str,
    notes: str | None,
) -> str:
    details = [
        f"Authorized Hydra result ingestion for {target_system} using {protocol}.",
        f"Summary: {result_summary.strip()}.",
    ]

    if notes:
        details.append(f"Notes: {notes.strip()}.")

    details.append("AegisCore stores imported credential-assessment results only and does not execute Hydra or automate attacks.")
    return " ".join(details)


def _confidence_score(severity: AlertSeverity) -> float:
    score_lookup = {
        AlertSeverity.CRITICAL: 0.94,
        AlertSeverity.HIGH: 0.86,
        AlertSeverity.MEDIUM: 0.74,
        AlertSeverity.LOW: 0.62,
    }
    return score_lookup[severity]


def get_hydra_status() -> dict:
    integration = get_augmented_integration_by_tool(IntegrationTool.HYDRA)
    latest_titles = get_latest_alert_titles_for_tool(IntegrationTool.HYDRA)

    return {
        **integration,
        "available_demo_payloads": 3,
        "latest_imported_alert_titles": latest_titles,
    }


def import_hydra_results(results: list[dict]) -> dict:
    imported_alert_count = 0
    imported_log_count = 0
    skipped_count = 0

    existing_references = set()
    for log_entry in load_log_records():
        if log_entry.get("source_tool") != IntegrationTool.HYDRA:
            continue

        if log_entry.get("integration_ref"):
            existing_references.add(log_entry["integration_ref"])

        raw_log = log_entry.get("raw_log")
        if isinstance(raw_log, dict):
            reference_payload = {
                "target_system": raw_log.get("target_system"),
                "protocol": raw_log.get("protocol"),
                "timestamp": raw_log.get("timestamp"),
                "result_summary": raw_log.get("result_summary"),
            }
            existing_references.add(_build_hydra_reference(reference_payload))

    for result_payload in results:
        integration_ref = _build_hydra_reference(result_payload)
        if integration_ref in existing_references:
            skipped_count += 1
            continue

        target_system = str(
            result_payload.get("target_system") or result_payload.get("target") or "unknown-lab-target"
        )
        protocol = str(result_payload.get("protocol") or "unknown-protocol")
        result_summary = str(result_payload.get("result_summary") or "Authorized lab assessment result imported")
        notes = str(result_payload.get("notes") or "").strip() or None
        timestamp = normalize_timestamp(result_payload.get("timestamp"))
        severity = _map_hydra_severity(result_summary, notes)
        finding_metadata = {
            "target_system": target_system,
            "protocol": protocol,
            "result_summary": result_summary,
            "assessment_scope": "authorized_lab_only_result_ingestion",
            "usage_boundary": "no_offensive_automation",
        }

        raw_log = {
            "target_system": target_system,
            "protocol": protocol,
            "timestamp": timestamp.isoformat(),
            "result_summary": result_summary,
            "notes": notes,
            "message": f"Authorized Hydra assessment result imported for {target_system}.",
            "assessment_scope": "Authorized assessment result ingestion",
            "usage_boundary": "No offensive automation",
        }

        create_log_record(
            {
                "source": target_system,
                "source_tool": IntegrationTool.HYDRA,
                "timestamp": timestamp,
                "severity": severity.value,
                "event_type": "credential_assessment",
                "raw_log": raw_log,
            },
            extra_fields={
                "integration_ref": integration_ref,
                "finding_metadata": finding_metadata,
                "parser_status": "normalized",
                "lab_only": True,
            },
        )
        imported_log_count += 1

        create_alert(
            title=_build_hydra_title(target_system, protocol),
            description=_build_hydra_description(target_system, protocol, result_summary, notes),
            source=target_system,
            source_tool=IntegrationTool.HYDRA,
            severity=severity,
            status_value=AlertStatus.NEW,
            confidence_score=round(_confidence_score(severity), 2),
            created_at=timestamp,
            extra_fields={
                "integration_ref": integration_ref,
                "finding_metadata": finding_metadata,
                "parser_status": "normalized",
                "lab_only": True,
            },
        )
        imported_alert_count += 1
        existing_references.add(integration_ref)

    last_import_at = utc_now()
    last_import_message = (
        f"Imported {imported_alert_count} Hydra findings and {imported_log_count} logs."
    )
    update_integration_runtime(
        IntegrationTool.HYDRA,
        status=IntegrationHealth.CONNECTED,
        last_sync_at=last_import_at,
        last_import_at=last_import_at,
        last_import_message=last_import_message,
        notes="Authorized credential-assessment result ingestion. No offensive automation.",
    )

    return {
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "skipped_count": skipped_count,
        "last_import_at": last_import_at,
        "message": last_import_message,
    }
