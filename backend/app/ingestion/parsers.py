from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.utils.log_normalization import normalize_log_payload, normalize_source_tool, normalize_timestamp


def _coerce_dict(payload: Mapping[str, object]) -> dict[str, Any]:
    return dict(payload)


def _wazuh_event_type(payload: dict[str, Any]) -> str:
    rule = payload.get("rule", {}) if isinstance(payload.get("rule"), dict) else {}
    groups = [str(item).lower() for item in rule.get("groups", [])]
    description = str(rule.get("description") or "").lower()
    full_log = str(payload.get("full_log") or "").lower()
    combined_text = " ".join([description, full_log, " ".join(groups)])

    if payload.get("syscheck") or any(
        keyword in groups for keyword in ("syscheck", "fim", "integrity", "configuration")
    ):
        return "file_integrity"
    if any(
        keyword in combined_text
        for keyword in ("useradd", "account created", "new user", "unauthorized user", "groupadd")
    ):
        return "user_account"
    if any(keyword in groups for keyword in ("authentication_failed", "auth", "sshd", "windows")):
        return "authentication"
    if any(keyword in groups for keyword in ("malware", "virus", "trojan", "defender")):
        return "malware"
    if any(keyword in groups for keyword in ("network", "firewall", "suricata")):
        return "network"
    if any(keyword in combined_text for keyword in ("sudo", "privilege", "root")):
        return "privilege_change"

    return "security_alert"


def _suricata_severity(payload: dict[str, Any]) -> int:
    alert = payload.get("alert", {}) if isinstance(payload.get("alert"), dict) else {}
    level_value = alert.get("severity")

    try:
        numeric_level = float(level_value) if level_value is not None else 3
    except (TypeError, ValueError):
        numeric_level = 3

    if numeric_level <= 1:
        return 10
    if numeric_level <= 2:
        return 8
    if numeric_level <= 3:
        return 5
    return 2


def _suricata_event_type(payload: dict[str, Any]) -> str:
    explicit_type = str(payload.get("event_type") or "").strip().lower()
    if explicit_type and explicit_type != "alert":
        return explicit_type.replace(" ", "_")

    alert = payload.get("alert", {}) if isinstance(payload.get("alert"), dict) else {}
    signature = str(alert.get("signature") or "").lower()
    category = str(alert.get("category") or "").lower()
    combined_text = " ".join([signature, category])

    if "scan" in combined_text or "recon" in combined_text:
        return "reconnaissance"
    if "dns" in combined_text:
        return "dns_alert"
    if "smb" in combined_text or "rdp" in combined_text:
        return "network"
    if "malware" in combined_text or "trojan" in combined_text:
        return "malware"

    return "alert"


def _nmap_severity(payload: dict[str, Any]) -> int:
    risky_ports = {23, 445, 3389, 5900, 5985, 5986}
    exposed_data_ports = {3306, 5432, 6379, 9200}
    port_values = set()

    for port_record in payload.get("open_ports", []):
        port_value = port_record
        if isinstance(port_record, dict):
            port_value = port_record.get("port")
        try:
            port_values.add(int(port_value))
        except (TypeError, ValueError):
            continue

    if port_values & risky_ports:
        return 10
    if port_values & exposed_data_ports:
        return 8
    if len(port_values) >= 4:
        return 5

    return 2


def _hydra_severity(payload: dict[str, Any]) -> int:
    result_summary = str(payload.get("result_summary") or "").lower()
    notes = str(payload.get("notes") or "").lower()
    combined_text = " ".join([result_summary, notes])

    if any(
        keyword in combined_text
        for keyword in ("valid credential", "valid login", "successful login", "credential match")
    ):
        return 10
    if any(
        keyword in combined_text
        for keyword in ("threshold", "repeated match", "multiple match", "lockout", "password reuse")
    ):
        return 8
    if any(keyword in combined_text for keyword in ("failed attempt", "failed login", "assessment")):
        return 5

    return 2


def parse_wazuh_event(payload: Mapping[str, object]) -> dict[str, object]:
    raw_payload = _coerce_dict(payload)
    agent = raw_payload.get("agent", {}) if isinstance(raw_payload.get("agent"), dict) else {}
    manager = raw_payload.get("manager", {}) if isinstance(raw_payload.get("manager"), dict) else {}
    source = str(agent.get("name") or manager.get("name") or "wazuh-agent")
    rule = raw_payload.get("rule", {}) if isinstance(raw_payload.get("rule"), dict) else {}
    syscheck = raw_payload.get("syscheck", {}) if isinstance(raw_payload.get("syscheck"), dict) else {}
    data = raw_payload.get("data", {}) if isinstance(raw_payload.get("data"), dict) else {}

    normalized_event = normalize_log_payload(
        {
            "source": source,
            "source_tool": "wazuh",
            "timestamp": raw_payload.get("timestamp") or raw_payload.get("@timestamp"),
            "severity": rule.get("level"),
            "event_type": _wazuh_event_type(raw_payload),
            "raw_log": {
                **raw_payload,
                "source_ip": data.get("srcip") or data.get("source_ip"),
                "user": data.get("user"),
                "path": syscheck.get("path"),
                "message": raw_payload.get("full_log") or rule.get("description") or "Imported Wazuh event",
            },
        }
    )

    return {
        "source": source,
        "source_tool": "wazuh",
        "event_type": normalized_event["event_type"],
        "severity": normalized_event["severity"],
        "created_at": normalized_event["created_at"],
        "title": str(rule.get("description") or "Imported Wazuh alert"),
        "message": normalized_event["normalized_log"]["message"],
        "normalized_event": normalized_event["normalized_log"],
        "parser_status": "normalized",
    }


def parse_suricata_event(payload: Mapping[str, object]) -> dict[str, object]:
    raw_payload = _coerce_dict(payload)
    alert = raw_payload.get("alert", {}) if isinstance(raw_payload.get("alert"), dict) else {}
    source = str(raw_payload.get("sensor_name") or raw_payload.get("host") or raw_payload.get("src_ip") or "suricata-sensor")

    normalized_event = normalize_log_payload(
        {
            "source": source,
            "source_tool": "suricata",
            "timestamp": raw_payload.get("timestamp"),
            "severity": _suricata_severity(raw_payload),
            "event_type": _suricata_event_type(raw_payload),
            "raw_log": {
                **raw_payload,
                "message": alert.get("signature") or raw_payload.get("message") or "Imported Suricata event",
            },
        }
    )

    return {
        "source": source,
        "source_tool": "suricata",
        "event_type": normalized_event["event_type"],
        "severity": normalized_event["severity"],
        "created_at": normalized_event["created_at"],
        "title": str(alert.get("signature") or "Imported Suricata network alert"),
        "message": normalized_event["normalized_log"]["message"],
        "normalized_event": normalized_event["normalized_log"],
        "parser_status": "normalized",
    }


def parse_lab_import(tool: str, payload: Mapping[str, object]) -> dict[str, object]:
    normalized_tool = normalize_source_tool(tool)
    raw_payload = _coerce_dict(payload)
    timestamp_value = raw_payload.get("timestamp") or raw_payload.get("scan_timestamp")

    if normalized_tool == "nmap":
        source = str(raw_payload.get("host") or "unknown-lab-host")
        raw_log = {
            **raw_payload,
            "message": f"Authorized Nmap lab result imported for {source}.",
            "assessment_scope": "authorized_lab_only_result_ingestion",
            "usage_boundary": "no_offensive_automation",
        }
        normalized_event = normalize_log_payload(
            {
                "source": source,
                "source_tool": normalized_tool,
                "timestamp": timestamp_value,
                "severity": _nmap_severity(raw_payload),
                "event_type": "scan_result",
                "raw_log": raw_log,
            }
        )
        title = f"Authorized Nmap result imported for {source}"
    elif normalized_tool == "hydra":
        source = str(raw_payload.get("target_system") or raw_payload.get("target") or "unknown-lab-target")
        raw_log = {
            **raw_payload,
            "message": f"Authorized Hydra lab result imported for {source}.",
            "assessment_scope": "authorized_lab_only_result_ingestion",
            "usage_boundary": "no_offensive_automation",
        }
        normalized_event = normalize_log_payload(
            {
                "source": source,
                "source_tool": normalized_tool,
                "timestamp": timestamp_value,
                "severity": _hydra_severity(raw_payload),
                "event_type": "credential_assessment",
                "raw_log": raw_log,
            }
        )
        title = f"Authorized Hydra result imported for {source}"
    else:
        source = str(raw_payload.get("source") or raw_payload.get("host") or f"{normalized_tool}-lab")
        raw_log = {
            **raw_payload,
            "message": str(raw_payload.get("message") or f"Authorized {normalized_tool} lab result imported."),
        }
        normalized_event = normalize_log_payload(
            {
                "source": source,
                "source_tool": normalized_tool,
                "timestamp": normalize_timestamp(timestamp_value),
                "severity": raw_payload.get("severity"),
                "event_type": raw_payload.get("event_type"),
                "raw_log": raw_log,
            }
        )
        title = f"Authorized {normalized_tool} result imported for {source}"

    return {
        "source": source,
        "source_tool": normalized_tool,
        "event_type": normalized_event["event_type"],
        "severity": normalized_event["severity"],
        "created_at": normalized_event["created_at"],
        "title": title,
        "message": normalized_event["normalized_log"]["message"],
        "normalized_event": normalized_event["normalized_log"],
        "lab_only": normalized_tool in {"nmap", "hydra"},
        "parser_status": "normalized",
    }
