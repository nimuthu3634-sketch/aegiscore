from __future__ import annotations

from app.core.enums import AlertSeverity, ResponseActionMode, ResponseActionType

AUTO_RESPONSE_ANOMALY_THRESHOLD = 0.78
AUTO_RESPONSE_CONFIDENCE_THRESHOLD = 0.9


def _combined_text(alert: dict) -> str:
    finding_metadata = alert.get("finding_metadata", {})
    if not isinstance(finding_metadata, dict):
        finding_metadata = {}

    text_values = [
        alert.get("title"),
        alert.get("description"),
        alert.get("event_type"),
        finding_metadata.get("event_type"),
        finding_metadata.get("signature"),
        finding_metadata.get("category"),
        finding_metadata.get("result_summary"),
        finding_metadata.get("scan_notes"),
        finding_metadata.get("path"),
        finding_metadata.get("username"),
    ]
    return " ".join(str(value).lower() for value in text_values if value)


def _threat_family(alert: dict) -> str | None:
    event_type = str(alert.get("event_type") or "").strip().lower()
    combined_text = _combined_text(alert)

    if event_type == "user_account" or any(
        keyword in combined_text
        for keyword in ("useradd", "account created", "new user", "unauthorized user", "groupadd")
    ):
        return "unauthorized_account_creation"

    if event_type == "file_integrity" or any(
        keyword in combined_text
        for keyword in ("file_integrity", "integrity", "syscheck", "sudoers", "checksum")
    ):
        return "file_integrity_violation"

    if event_type in {"authentication", "credential_assessment"} or any(
        keyword in combined_text
        for keyword in ("failed password", "brute", "hydra", "credential match", "lockout")
    ):
        return "brute_force_attack"

    if event_type in {"reconnaissance", "scan_result"} or any(
        keyword in combined_text
        for keyword in ("port scan", "scan result", "recon", "nmap", "exposes tcp/", "exposed management port")
    ):
        return "port_scan"

    return None


def _is_high_risk(alert: dict) -> bool:
    severity = alert.get("severity")
    anomaly_score = float(alert.get("anomaly_score", 0.0) or 0.0)
    confidence_score = float(alert.get("confidence_score", 0.0) or 0.0)

    return (
        severity == AlertSeverity.CRITICAL
        or anomaly_score >= AUTO_RESPONSE_ANOMALY_THRESHOLD
        or (
            severity == AlertSeverity.HIGH
            and confidence_score >= AUTO_RESPONSE_CONFIDENCE_THRESHOLD
        )
    )


def _finding_metadata(alert: dict) -> dict:
    finding_metadata = alert.get("finding_metadata", {})
    return finding_metadata if isinstance(finding_metadata, dict) else {}


def _planned_actions(alert: dict, threat_family: str) -> list[tuple[ResponseActionType, str]]:
    finding_metadata = _finding_metadata(alert)
    action_plan: list[tuple[ResponseActionType, str]] = [
        (
            ResponseActionType.CREATE_INCIDENT,
            f"Automated lab escalation created an incident for the {threat_family.replace('_', ' ')} finding.",
        ),
        (
            ResponseActionType.MARK_INVESTIGATING,
            "Automated lab workflow moved the alert into investigating for analyst review.",
        ),
    ]

    if threat_family in {"brute_force_attack", "port_scan"} and finding_metadata.get("source_ip"):
        action_plan.append(
            (
                ResponseActionType.BLOCK_SOURCE_IP,
                "Automated lab response recorded a temporary source IP block for a high-risk network-originating alert.",
            )
        )

    if threat_family == "file_integrity_violation":
        action_plan.append(
            (
                ResponseActionType.ISOLATE_ASSET,
                "Automated lab response recorded host isolation for a high-risk file integrity finding.",
            )
        )

    if threat_family == "unauthorized_account_creation" and finding_metadata.get("username"):
        action_plan.append(
            (
                ResponseActionType.DISABLE_ACCOUNT,
                "Automated lab response recorded account disablement for an unauthorized account-creation alert.",
            )
        )

    return action_plan


def apply_automated_response(alert: dict) -> list[dict]:
    threat_family = _threat_family(alert)
    if threat_family is None or not _is_high_risk(alert):
        return []

    from app.services.response_actions import execute_response_action

    actions: list[dict] = []
    for action_type, notes in _planned_actions(alert, threat_family):
        actions.append(
            execute_response_action(
                alert_id=alert["id"],
                action_type=action_type,
                actor=None,
                notes=notes,
                execution_mode=ResponseActionMode.AUTOMATED,
            )
        )

    return actions
