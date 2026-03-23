from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.enums import AlertSeverity
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


LANL_PARSER_REFERENCE_TS = "2026-01-01T00:00:00Z"
LANL_FAILURE_VALUES = {"0", "f", "fail", "failed", "failure", "false", "denied"}
LANL_SENSITIVE_PORTS = {22, 23, 445, 3389, 5985, 5986, 1433, 3306, 5432, 6379}


def _parse_lanl_int(value: str) -> int:
    cleaned_value = value.strip()
    if not cleaned_value:
        raise ValueError("LANL record field was empty.")
    return int(cleaned_value)


def _parse_lanl_port(value: str) -> int | None:
    cleaned_value = value.strip()
    if not cleaned_value or not cleaned_value.isdigit():
        return None
    return int(cleaned_value)


def _normalize_lanl_user(value: str) -> str:
    cleaned_value = value.strip().lower()
    return cleaned_value.split("@", 1)[0] if "@" in cleaned_value else cleaned_value


def parse_lanl_auth_record(row: list[str], *, redteam_match: bool = False) -> dict[str, object]:
    if len(row) < 9:
        raise ValueError("LANL auth records must contain 9 columns.")

    relative_time_seconds = _parse_lanl_int(row[0])
    source_user = row[1].strip()
    destination_user = row[2].strip()
    source_computer = row[3].strip() or "lanl-auth-source"
    destination_computer = row[4].strip() or "lanl-auth-target"
    authentication_type = row[5].strip()
    logon_type = row[6].strip()
    auth_orientation = row[7].strip()
    auth_outcome = row[8].strip()
    auth_success = auth_outcome.strip().lower() not in LANL_FAILURE_VALUES

    severity = (
        AlertSeverity.CRITICAL
        if redteam_match
        else AlertSeverity.HIGH
        if not auth_success
        else AlertSeverity.MEDIUM
    )
    event_type = "compromise" if redteam_match else "authentication"
    message = (
        f"LANL auth event {source_user or 'unknown-user'} from {source_computer} "
        f"to {destination_computer} ended with {auth_outcome or 'unknown'}."
    )
    raw_log = {
        "relative_time_seconds": relative_time_seconds,
        "source_user": source_user,
        "destination_user": destination_user,
        "source_computer": source_computer,
        "destination_computer": destination_computer,
        "authentication_type": authentication_type,
        "logon_type": logon_type,
        "auth_orientation": auth_orientation,
        "auth_outcome": auth_outcome,
        "redteam_match": redteam_match,
        "message": message,
        "source_ip": source_computer,
        "destination_ip": destination_computer,
        "user": _normalize_lanl_user(source_user) or source_user,
    }
    normalized_event = normalize_log_payload(
        {
            "source": source_computer,
            "source_tool": "lanl",
            "timestamp": LANL_PARSER_REFERENCE_TS,
            "severity": severity.value,
            "event_type": event_type,
            "raw_log": raw_log,
        }
    )

    return {
        "source": source_computer,
        "source_tool": "lanl",
        "event_type": event_type,
        "severity": severity,
        "relative_time_seconds": relative_time_seconds,
        "title": (
            "Known red-team authentication path observed in LANL data"
            if redteam_match
            else "Failed authentication activity observed in LANL data"
            if not auth_success
            else "LANL authentication event imported"
        ),
        "message": message,
        "normalized_event": normalized_event["normalized_log"],
        "raw_event": raw_log,
        "finding_metadata": {
            "dataset_source": "lanl_comprehensive",
            "dataset_type": "auth",
            "relative_time_seconds": relative_time_seconds,
            "source_user": source_user,
            "destination_user": destination_user,
            "source_computer": source_computer,
            "destination_computer": destination_computer,
            "authentication_type": authentication_type,
            "logon_type": logon_type,
            "auth_orientation": auth_orientation,
            "auth_outcome": auth_outcome,
            "redteam_match": redteam_match,
            "event_type": event_type,
        },
        "parser_status": "normalized",
        "lab_only": False,
    }


def parse_lanl_dns_record(row: list[str]) -> dict[str, object]:
    if len(row) < 3:
        raise ValueError("LANL DNS records must contain 3 columns.")

    relative_time_seconds = _parse_lanl_int(row[0])
    source_computer = row[1].strip() or "lanl-dns-source"
    resolved_name = row[2].strip() or "unknown-destination"
    message = f"LANL DNS record: {source_computer} resolved {resolved_name}."
    raw_log = {
        "relative_time_seconds": relative_time_seconds,
        "source_computer": source_computer,
        "resolved_name": resolved_name,
        "message": message,
        "source_ip": source_computer,
        "destination_ip": resolved_name,
    }
    normalized_event = normalize_log_payload(
        {
            "source": source_computer,
            "source_tool": "lanl",
            "timestamp": LANL_PARSER_REFERENCE_TS,
            "severity": AlertSeverity.LOW.value,
            "event_type": "dns_resolution",
            "raw_log": raw_log,
        }
    )

    return {
        "source": source_computer,
        "source_tool": "lanl",
        "event_type": "dns_resolution",
        "severity": AlertSeverity.LOW,
        "relative_time_seconds": relative_time_seconds,
        "title": "LANL DNS event imported",
        "message": message,
        "normalized_event": normalized_event["normalized_log"],
        "raw_event": raw_log,
        "finding_metadata": {
            "dataset_source": "lanl_comprehensive",
            "dataset_type": "dns",
            "relative_time_seconds": relative_time_seconds,
            "source_computer": source_computer,
            "resolved_name": resolved_name,
            "event_type": "dns_resolution",
        },
        "parser_status": "normalized",
        "lab_only": False,
    }


def parse_lanl_flow_record(row: list[str]) -> dict[str, object]:
    if len(row) < 9:
        raise ValueError("LANL flow records must contain 9 columns.")

    relative_time_seconds = _parse_lanl_int(row[0])
    duration_seconds = _parse_lanl_int(row[1])
    source_computer = row[2].strip() or "lanl-flow-source"
    source_port = row[3].strip()
    destination_computer = row[4].strip() or "lanl-flow-target"
    destination_port = row[5].strip()
    protocol = row[6].strip().lower() or "unknown"
    packet_count = _parse_lanl_int(row[7])
    byte_count = _parse_lanl_int(row[8])
    numeric_destination_port = _parse_lanl_port(destination_port)
    severity = (
        AlertSeverity.HIGH
        if numeric_destination_port in LANL_SENSITIVE_PORTS or byte_count >= 10_000_000
        else AlertSeverity.MEDIUM
        if duration_seconds >= 3600 or packet_count >= 10_000
        else AlertSeverity.LOW
    )
    message = (
        f"LANL flow from {source_computer}:{source_port} to "
        f"{destination_computer}:{destination_port} used {protocol.upper()}."
    )
    raw_log = {
        "relative_time_seconds": relative_time_seconds,
        "duration_seconds": duration_seconds,
        "source_computer": source_computer,
        "source_port": source_port,
        "destination_computer": destination_computer,
        "destination_port": destination_port,
        "protocol": protocol,
        "packet_count": packet_count,
        "byte_count": byte_count,
        "message": message,
        "source_ip": source_computer,
        "destination_ip": destination_computer,
        "port": destination_port,
    }
    normalized_event = normalize_log_payload(
        {
            "source": source_computer,
            "source_tool": "lanl",
            "timestamp": LANL_PARSER_REFERENCE_TS,
            "severity": severity.value,
            "event_type": "network_flow",
            "raw_log": raw_log,
        }
    )

    return {
        "source": source_computer,
        "source_tool": "lanl",
        "event_type": "network_flow",
        "severity": severity,
        "relative_time_seconds": relative_time_seconds,
        "title": "LANL network flow imported",
        "message": message,
        "normalized_event": normalized_event["normalized_log"],
        "raw_event": raw_log,
        "finding_metadata": {
            "dataset_source": "lanl_comprehensive",
            "dataset_type": "flows",
            "relative_time_seconds": relative_time_seconds,
            "duration_seconds": duration_seconds,
            "source_computer": source_computer,
            "source_port": source_port,
            "destination_computer": destination_computer,
            "destination_port": destination_port,
            "protocol": protocol,
            "packet_count": packet_count,
            "byte_count": byte_count,
            "sensitive_port_match": numeric_destination_port in LANL_SENSITIVE_PORTS,
            "event_type": "network_flow",
        },
        "parser_status": "normalized",
        "lab_only": False,
    }


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
