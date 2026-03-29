from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from app.models.entities import AlertSeverity


def _load_payload(raw_bytes: bytes) -> Any:
    return json.loads(raw_bytes.decode("utf-8"))


def _severity_from_wazuh(level: int | float | None) -> AlertSeverity:
    numeric = int(level or 0)
    if numeric >= 12:
        return AlertSeverity.CRITICAL
    if numeric >= 8:
        return AlertSeverity.HIGH
    if numeric >= 5:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _severity_from_suricata(level: int | float | None) -> AlertSeverity:
    numeric = int(level or 4)
    if numeric <= 1:
        return AlertSeverity.CRITICAL
    if numeric == 2:
        return AlertSeverity.HIGH
    if numeric == 3:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _as_iterable(payload: Any, key: str | None = None) -> Iterable:
    if isinstance(payload, list):
        return payload
    if key and isinstance(payload, dict):
        value = payload.get(key, [])
        if isinstance(value, list):
            return value
    return []


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def parse_telemetry(source: str, raw_bytes: bytes) -> list[dict[str, Any]]:
    payload = _load_payload(raw_bytes)
    source = source.lower()

    if source == "wazuh":
        return [
            {
                "title": item.get("rule", {}).get("description", "Wazuh alert"),
                "description": item.get("full_log") or "Imported Wazuh defensive telemetry",
                "source": "wazuh",
                "source_type": "endpoint-telemetry",
                "event_type": "wazuh-rule",
                "severity": _severity_from_wazuh(item.get("rule", {}).get("level")).value,
                "occurred_at": _parse_timestamp(item.get("timestamp")),
                "asset_hostname": item.get("agent", {}).get("name") or "unknown-host",
                "asset_ip": item.get("data", {}).get("srcip"),
                "tags": item.get("rule", {}).get("groups", []),
                "message": item.get("full_log") or item.get("rule", {}).get("description", "Wazuh event"),
                "level": "warning",
                "category": "endpoint",
                "raw_payload": item,
                "parsed_payload": {
                    "rule_id": item.get("rule", {}).get("id"),
                    "rule_level": item.get("rule", {}).get("level"),
                    "user": item.get("data", {}).get("user"),
                },
                "incident_candidate": _severity_from_wazuh(item.get("rule", {}).get("level"))
                in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
            }
            for item in _as_iterable(payload, "alerts")
        ]

    if source == "suricata":
        return [
            {
                "title": item.get("alert", {}).get("signature", "Suricata alert"),
                "description": item.get("alert", {}).get("category", "Imported Suricata network alert"),
                "source": "suricata",
                "source_type": "network-telemetry",
                "event_type": item.get("event_type", "suricata-alert"),
                "severity": _severity_from_suricata(item.get("alert", {}).get("severity")).value,
                "occurred_at": _parse_timestamp(item.get("timestamp")),
                "asset_hostname": item.get("dest_ip") or "network-target",
                "asset_ip": item.get("dest_ip"),
                "tags": [item.get("event_type", "alert"), item.get("proto", "unknown"), item.get("sensor_name", "sensor")],
                "message": item.get("alert", {}).get("signature", "Suricata event"),
                "level": "warning",
                "category": "network",
                "raw_payload": item,
                "parsed_payload": {
                    "source_ip": item.get("src_ip"),
                    "destination_ip": item.get("dest_ip"),
                    "destination_port": item.get("dest_port"),
                },
                "incident_candidate": _severity_from_suricata(item.get("alert", {}).get("severity"))
                in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
            }
            for item in _as_iterable(payload, "events")
        ]

    if source == "nmap":
        parsed_items = []
        for item in _as_iterable(payload):
            ports = item.get("open_ports", [])
            risky_ports = {22, 23, 445, 3389, 5985, 5986}
            exposed_ports = {entry.get("port") for entry in ports if isinstance(entry, dict)}
            severity = (
                AlertSeverity.HIGH
                if risky_ports.intersection(exposed_ports)
                else AlertSeverity.MEDIUM
                if len(exposed_ports) >= 3
                else AlertSeverity.LOW
            )
            parsed_items.append(
                {
                    "title": f"Nmap import: {item.get('host', 'asset')} exposure review",
                    "description": item.get(
                        "scan_notes", "Imported lab-safe Nmap result. No scan execution performed by AegisCore."
                    ),
                    "source": "nmap",
                    "source_type": "lab-import",
                    "event_type": "nmap-import",
                    "severity": severity.value,
                    "occurred_at": None,
                    "asset_hostname": item.get("host", "unknown-host"),
                    "asset_ip": None,
                    "tags": item.get("service_names", []),
                    "message": f"Imported Nmap result with {len(ports)} exposed services",
                    "level": "info",
                    "category": "exposure",
                    "raw_payload": item,
                    "parsed_payload": {"open_ports": ports, "service_names": item.get("service_names", [])},
                    "incident_candidate": severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
                }
            )
        return parsed_items

    if source == "hydra":
        parsed_items = []
        for item in _as_iterable(payload):
            summary = str(item.get("result_summary", "Imported Hydra lab result"))
            text = summary.lower()
            if "valid credential" in text or "password reuse" in text:
                severity = AlertSeverity.HIGH
            elif "lockout" in text:
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
            parsed_items.append(
                {
                    "title": f"Hydra result import: {item.get('target_system', 'target')}",
                    "description": item.get(
                        "notes", "Imported lab-safe Hydra output. No execution performed by AegisCore."
                    ),
                    "source": "hydra",
                    "source_type": "lab-import",
                    "event_type": "hydra-import",
                    "severity": severity.value,
                    "occurred_at": None,
                    "asset_hostname": item.get("target_system", "unknown-target"),
                    "asset_ip": None,
                    "tags": [item.get("protocol", "protocol")],
                    "message": summary,
                    "level": "warning" if severity != AlertSeverity.LOW else "info",
                    "category": "credential-exposure",
                    "raw_payload": item,
                    "parsed_payload": {"protocol": item.get("protocol"), "summary": summary},
                    "incident_candidate": severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
                }
            )
        return parsed_items

    raise ValueError(f"Unsupported integration source: {source}")
