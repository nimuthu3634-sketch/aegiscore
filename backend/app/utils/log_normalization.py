from datetime import datetime, timezone
from typing import Any

from app.core.enums import AlertSeverity
from app.utils.time import utc_now

SEVERITY_MAP = {
    "critical": AlertSeverity.CRITICAL,
    "crit": AlertSeverity.CRITICAL,
    "fatal": AlertSeverity.CRITICAL,
    "emergency": AlertSeverity.CRITICAL,
    "alert": AlertSeverity.CRITICAL,
    "high": AlertSeverity.HIGH,
    "error": AlertSeverity.HIGH,
    "err": AlertSeverity.HIGH,
    "medium": AlertSeverity.MEDIUM,
    "warning": AlertSeverity.MEDIUM,
    "warn": AlertSeverity.MEDIUM,
    "notice": AlertSeverity.MEDIUM,
    "low": AlertSeverity.LOW,
    "info": AlertSeverity.LOW,
    "informational": AlertSeverity.LOW,
    "debug": AlertSeverity.LOW,
}

TIMESTAMP_KEYS = ("timestamp", "time", "created_at", "event_time", "@timestamp")


def normalize_source_tool(source_tool: str) -> str:
    return source_tool.strip().lower().replace(" ", "_")


def normalize_timestamp(value: str | int | float | datetime | None) -> datetime:
    if value is None:
        return utc_now()

    if isinstance(value, datetime):
        parsed_value = value
    elif isinstance(value, (int, float)):
        timestamp_value = value / 1000 if value > 1_000_000_000_000 else value
        parsed_value = datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
    else:
        cleaned_value = value.strip()
        if cleaned_value.replace(".", "", 1).isdigit():
            return normalize_timestamp(float(cleaned_value))

        if cleaned_value.endswith("Z"):
            cleaned_value = cleaned_value[:-1] + "+00:00"

        try:
            parsed_value = datetime.fromisoformat(cleaned_value)
        except ValueError:
            return utc_now()
        if parsed_value.tzinfo is None:
            parsed_value = parsed_value.replace(tzinfo=timezone.utc)

    return parsed_value.astimezone(timezone.utc)


def normalize_severity(value: str | int | float | None) -> AlertSeverity:
    if isinstance(value, (int, float)):
        numeric_value = float(value)
        if numeric_value >= 9:
            return AlertSeverity.CRITICAL
        if numeric_value >= 7:
            return AlertSeverity.HIGH
        if numeric_value >= 4:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW

    if value is None:
        return AlertSeverity.LOW

    normalized_value = str(value).strip().lower()
    if normalized_value.replace(".", "", 1).isdigit():
        return normalize_severity(float(normalized_value))

    return SEVERITY_MAP.get(normalized_value, AlertSeverity.LOW)


def identify_event_type(source_tool: str, raw_log: dict[str, Any], explicit_event_type: str | None) -> str:
    if explicit_event_type:
        return explicit_event_type.strip().lower().replace(" ", "_")

    normalized_tool = normalize_source_tool(source_tool)
    if normalized_tool == "nmap":
        return "scan_result"
    if normalized_tool == "hydra":
        return "credential_assessment"

    message = " ".join(str(value) for value in raw_log.values()).lower()
    if any(
        keyword in message
        for keyword in ("integrity", "checksum", "syscheck", "file changed", "file modified", "sudoers")
    ):
        return "file_integrity"
    if any(
        keyword in message
        for keyword in ("useradd", "account created", "new user", "groupadd", "unauthorized user")
    ):
        return "user_account"
    if any(keyword in message for keyword in ("login", "ssh", "rdp", "password", "sudo", "auth")):
        return "authentication"
    if any(keyword in message for keyword in ("dns", "tls", "network", "traffic", "port", "smb")):
        return "network"
    if any(keyword in message for keyword in ("malware", "quarantine", "trojan", "ransomware")):
        return "malware"
    if any(keyword in message for keyword in ("policy", "config", "snapshot", "baseline", "drift")):
        return "configuration"

    return "other"


def infer_source(raw_log: dict[str, Any], explicit_source: str | None) -> str:
    if explicit_source:
        return explicit_source

    for key in ("source", "host", "hostname", "asset", "device", "sensor"):
        if raw_log.get(key):
            return str(raw_log[key])

    return "unknown-source"


def extract_message(raw_log: dict[str, Any]) -> str:
    for key in ("message", "log", "event", "summary", "description", "alert"):
        if raw_log.get(key):
            return str(raw_log[key])

    return "Lab security log event"


def normalize_log_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw_log = payload["raw_log"]
    timestamp_candidate = payload.get("timestamp")
    if timestamp_candidate is None:
        for key in TIMESTAMP_KEYS:
            if raw_log.get(key) is not None:
                timestamp_candidate = raw_log[key]
                break

    severity_candidate = payload.get("severity")
    if severity_candidate is None:
        for key in ("severity", "level", "priority", "alert_level"):
            if raw_log.get(key) is not None:
                severity_candidate = raw_log[key]
                break

    source_tool = normalize_source_tool(payload["source_tool"])
    created_at = normalize_timestamp(timestamp_candidate)
    severity = normalize_severity(severity_candidate)
    event_type = identify_event_type(source_tool, raw_log, payload.get("event_type"))
    source = infer_source(raw_log, payload.get("source"))
    message = extract_message(raw_log)

    observables = {
        "actor": raw_log.get("user") or raw_log.get("username"),
        "source_ip": raw_log.get("source_ip") or raw_log.get("src_ip"),
        "destination_ip": raw_log.get("destination_ip") or raw_log.get("dest_ip") or raw_log.get("dst_ip"),
        "port": raw_log.get("port") or raw_log.get("dest_port") or raw_log.get("dport"),
        "path": raw_log.get("path"),
        "file": raw_log.get("file"),
        "action": raw_log.get("action"),
        "protocol": raw_log.get("proto") or raw_log.get("protocol"),
    }

    normalized_log = {
        "timestamp": created_at.isoformat(),
        "severity": severity.value,
        "event_type": event_type,
        "source": source,
        "source_tool": source_tool,
        "message": message,
        "observables": {key: value for key, value in observables.items() if value is not None},
        "original_keys": sorted(raw_log.keys()),
    }

    return {
        "source": source,
        "source_tool": source_tool,
        "raw_log": raw_log,
        "normalized_log": normalized_log,
        "event_type": event_type,
        "severity": severity,
        "created_at": created_at,
    }
