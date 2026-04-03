from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import datetime
from typing import Any
from xml.etree import ElementTree

from app.ingestion.normalization import LAB_ONLY_IMPORT_SOURCES, NormalizedRecord, ParseResult
from app.models.entities import AlertSeverity


HYDRA_SUCCESS_PATTERN = re.compile(
    r"^\[(?P<port>\d+)\]\[(?P<protocol>[^\]]+)\]\s+host:\s+(?P<host>\S+)\s+login:\s+(?P<login>\S+)\s+password:\s+(?P<password>.+)$",
    re.IGNORECASE,
)


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


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


def _severity_from_nmap(open_ports: list[dict[str, Any]]) -> AlertSeverity:
    risky_ports = {21, 22, 23, 445, 3389, 5985, 5986}
    exposed_ports = {int(entry["port"]) for entry in open_ports if entry.get("port") and str(entry.get("state", "open")).lower() == "open"}
    if risky_ports.intersection(exposed_ports):
        return AlertSeverity.HIGH
    if len(exposed_ports) >= 5:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _severity_from_hydra(summary: str) -> AlertSeverity:
    lowered = summary.lower()
    if "valid credential" in lowered or "valid password" in lowered or "password reuse" in lowered:
        return AlertSeverity.HIGH
    if "lockout" in lowered or "threshold" in lowered:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _load_json_or_ndjson(raw_bytes: bytes) -> tuple[Any, str]:
    text = raw_bytes.decode("utf-8").strip()
    if not text:
        return [], "json"

    if text[0] in "[{":
        return json.loads(text), "json"

    items = [json.loads(line) for line in text.splitlines() if line.strip()]
    return items, "ndjson"


def _as_iterable(payload: Any, key: str | None = None) -> Iterable[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        if key and isinstance(payload.get(key), list):
            return payload[key]
        if isinstance(payload.get("items"), list):
            return payload["items"]
    return []


def _parse_nmap_json(payload: Any) -> list[dict[str, Any]]:
    items = list(_as_iterable(payload, "hosts"))
    if not items and isinstance(payload, dict):
        items = [payload]

    parsed_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        host = item.get("host") or item.get("hostname") or item.get("ip_address") or "unknown-host"
        ports = [entry for entry in item.get("open_ports", []) if isinstance(entry, dict)]
        parsed_items.append(
            {
                "host": host,
                "ip_address": item.get("ip_address"),
                "operating_system": item.get("operating_system"),
                "open_ports": ports,
                "service_names": item.get("service_names") or [entry.get("service_name") for entry in ports if entry.get("service_name")],
                "scan_timestamp": item.get("scan_timestamp") or item.get("timestamp"),
                "scan_notes": item.get("scan_notes"),
            }
        )
    return parsed_items


def _parse_nmap_xml(raw_bytes: bytes) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(raw_bytes.decode("utf-8"))
    parsed_items: list[dict[str, Any]] = []
    for host in root.findall("host"):
        status = host.find("status")
        if status is not None and status.attrib.get("state") != "up":
            continue

        ip_address = None
        for address in host.findall("address"):
            if address.attrib.get("addrtype") in {"ipv4", "ipv6"}:
                ip_address = address.attrib.get("addr")
                break

        hostname = None
        hostname_node = host.find("hostnames/hostname")
        if hostname_node is not None:
            hostname = hostname_node.attrib.get("name")

        operating_system = None
        osmatch = host.find("os/osmatch")
        if osmatch is not None:
            operating_system = osmatch.attrib.get("name")

        open_ports: list[dict[str, Any]] = []
        service_names: list[str] = []
        for port in host.findall("ports/port"):
            state = port.find("state")
            if state is None or state.attrib.get("state") != "open":
                continue
            service = port.find("service")
            service_name = service.attrib.get("name") if service is not None else None
            if service_name:
                service_names.append(service_name)
            open_ports.append(
                {
                    "port": int(port.attrib.get("portid", 0)),
                    "protocol": port.attrib.get("protocol", "tcp"),
                    "service_name": service_name,
                    "state": "open",
                }
            )

        if not open_ports:
            continue

        parsed_items.append(
            {
                "host": hostname or ip_address or "unknown-host",
                "ip_address": ip_address,
                "operating_system": operating_system,
                "open_ports": open_ports,
                "service_names": service_names,
                "scan_timestamp": root.attrib.get("startstr"),
                "scan_notes": "Imported Nmap XML result. No scan execution performed by AegisCore.",
            }
        )
    return parsed_items


def _parse_hydra_json(payload: Any) -> list[dict[str, Any]]:
    items = list(_as_iterable(payload, "results"))
    if not items and isinstance(payload, dict):
        items = [payload]

    parsed_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        parsed_items.append(
            {
                "target_system": item.get("target_system") or item.get("host") or "unknown-target",
                "protocol": item.get("protocol") or item.get("service") or "unknown",
                "result_summary": str(item.get("result_summary") or item.get("summary") or "Imported Hydra lab result"),
                "timestamp": item.get("timestamp"),
                "notes": item.get("notes"),
                "username": item.get("username"),
                "password": item.get("password"),
            }
        )
    return parsed_items


def _parse_hydra_text(raw_bytes: bytes) -> list[dict[str, Any]]:
    text = raw_bytes.decode("utf-8", errors="ignore")
    parsed_items: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        match = HYDRA_SUCCESS_PATTERN.match(line)
        if match:
            parsed_items.append(
                {
                    "target_system": match.group("host"),
                    "protocol": match.group("protocol"),
                    "result_summary": (
                        f"Imported Hydra lab result recorded a valid credential for {match.group('login')} on {match.group('host')}."
                    ),
                    "timestamp": None,
                    "notes": "Parsed from Hydra text output. No execution performed by AegisCore.",
                    "username": match.group("login"),
                    "password": match.group("password").strip(),
                }
            )
            continue

        lowered = line.lower()
        if "valid password" in lowered or "0 valid password" in lowered or "lockout" in lowered:
            parsed_items.append(
                {
                    "target_system": "hydra-import",
                    "protocol": "unknown",
                    "result_summary": line,
                    "timestamp": None,
                    "notes": "Parsed from Hydra text output. No execution performed by AegisCore.",
                    "username": None,
                    "password": None,
                }
            )
    return parsed_items


def _normalize_wazuh_records(payload: Any) -> list[NormalizedRecord]:
    normalized: list[NormalizedRecord] = []
    for item in _as_iterable(payload, "alerts"):
        if not isinstance(item, dict):
            continue
        severity = _severity_from_wazuh(item.get("rule", {}).get("level"))
        normalized.append(
            NormalizedRecord(
                external_id=item.get("id") or str(item.get("rule", {}).get("id") or ""),
                title=item.get("rule", {}).get("description", "Wazuh alert"),
                description=item.get("full_log") or "Imported Wazuh defensive telemetry",
                source="wazuh",
                source_type="endpoint-telemetry",
                event_type="wazuh-rule",
                severity=severity,
                occurred_at=_parse_timestamp(item.get("timestamp")),
                asset_hostname=item.get("agent", {}).get("name") or item.get("agent", {}).get("id"),
                asset_ip=item.get("agent", {}).get("ip") or item.get("data", {}).get("srcip"),
                tags=[*(item.get("rule", {}).get("groups") or []), "wazuh"],
                message=item.get("full_log") or item.get("rule", {}).get("description", "Wazuh event"),
                level="critical" if severity == AlertSeverity.CRITICAL else "warning",
                category=(item.get("rule", {}).get("groups") or ["endpoint"])[0],
                raw_payload=item,
                parsed_payload={
                    "rule_id": item.get("rule", {}).get("id"),
                    "rule_level": item.get("rule", {}).get("level"),
                    "manager": item.get("manager", {}).get("name"),
                    "user": item.get("data", {}).get("user"),
                    "src_ip": item.get("data", {}).get("srcip"),
                },
                incident_candidate=severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
                operating_system=item.get("agent", {}).get("os", {}).get("name"),
            ).finalize()
        )
    return normalized


def _normalize_suricata_records(payload: Any) -> list[NormalizedRecord]:
    normalized: list[NormalizedRecord] = []
    for item in _as_iterable(payload, "events"):
        if not isinstance(item, dict):
            continue
        severity = _severity_from_suricata(item.get("alert", {}).get("severity"))
        destination = item.get("dest_ip")
        normalized.append(
            NormalizedRecord(
                external_id=str(item.get("flow_id") or item.get("alert", {}).get("signature_id") or ""),
                title=item.get("alert", {}).get("signature", "Suricata alert"),
                description=item.get("alert", {}).get("category", "Imported Suricata network event"),
                source="suricata",
                source_type="network-telemetry",
                event_type=item.get("event_type", "suricata-alert"),
                severity=severity,
                occurred_at=_parse_timestamp(item.get("timestamp")),
                asset_hostname=destination or item.get("dest_host"),
                asset_ip=destination,
                tags=[item.get("event_type", "alert"), item.get("proto", "unknown"), item.get("sensor_name", "sensor"), "suricata"],
                message=item.get("alert", {}).get("signature", "Suricata event"),
                level="critical" if severity == AlertSeverity.CRITICAL else "warning",
                category=item.get("alert", {}).get("category", "network"),
                raw_payload=item,
                parsed_payload={
                    "src_ip": item.get("src_ip"),
                    "src_port": item.get("src_port"),
                    "dest_ip": item.get("dest_ip"),
                    "dest_port": item.get("dest_port"),
                    "protocol": item.get("proto"),
                    "sensor_name": item.get("sensor_name"),
                    "signature_id": item.get("alert", {}).get("signature_id"),
                },
                incident_candidate=severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
            ).finalize()
        )
    return normalized


def _normalize_nmap_records(items: list[dict[str, Any]]) -> list[NormalizedRecord]:
    normalized: list[NormalizedRecord] = []
    for item in items:
        open_ports = item.get("open_ports", [])
        severity = _severity_from_nmap(open_ports)
        findings = [
            {
                "type": "open-port",
                "port": entry.get("port"),
                "protocol": entry.get("protocol"),
                "service_name": entry.get("service_name"),
                "state": entry.get("state"),
            }
            for entry in open_ports
        ]
        normalized.append(
            NormalizedRecord(
                external_id=None,
                title=f"Nmap import: {item.get('host', 'asset')} exposure review",
                description=item.get("scan_notes") or "Imported Nmap lab output. No scan execution performed by AegisCore.",
                source="nmap",
                source_type="lab-import",
                event_type="nmap-import",
                severity=severity,
                occurred_at=_parse_timestamp(item.get("scan_timestamp")),
                asset_hostname=item.get("host"),
                asset_ip=item.get("ip_address"),
                tags=[*(item.get("service_names") or []), "lab-imported", "nmap"],
                message=f"Imported Nmap result with {len(open_ports)} exposed services",
                level="warning" if severity != AlertSeverity.LOW else "info",
                category="exposure",
                raw_payload=item,
                parsed_payload={
                    "open_ports": open_ports,
                    "service_names": item.get("service_names") or [],
                    "findings": findings,
                    "finding_count": len(findings),
                },
                incident_candidate=severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
                operating_system=item.get("operating_system"),
                imported_lab_data=True,
            ).finalize()
        )
    return normalized


def _normalize_hydra_records(items: list[dict[str, Any]]) -> list[NormalizedRecord]:
    normalized: list[NormalizedRecord] = []
    for item in items:
        summary = str(item.get("result_summary") or "Imported Hydra lab result")
        severity = _severity_from_hydra(summary)
        username = item.get("username")
        password = item.get("password")
        normalized.append(
            NormalizedRecord(
                external_id=None,
                title=f"Hydra import: {item.get('target_system', 'target')} credential review",
                description=item.get("notes") or "Imported Hydra lab output. No execution performed by AegisCore.",
                source="hydra",
                source_type="lab-import",
                event_type="hydra-import",
                severity=severity,
                occurred_at=_parse_timestamp(item.get("timestamp")),
                asset_hostname=item.get("target_system"),
                asset_ip=item.get("target_ip"),
                tags=[item.get("protocol", "protocol"), "lab-imported", "hydra"],
                message=summary,
                level="warning" if severity != AlertSeverity.LOW else "info",
                category="credential-exposure",
                raw_payload=item,
                parsed_payload={
                    "protocol": item.get("protocol"),
                    "summary": summary,
                    "username": username,
                    "has_password_match": bool(password),
                },
                incident_candidate=severity in {AlertSeverity.CRITICAL, AlertSeverity.HIGH},
                imported_lab_data=True,
            ).finalize()
        )
    return normalized


def parse_telemetry(source: str, raw_bytes: bytes, filename: str | None = None) -> ParseResult:
    source = source.lower()
    if source == "wazuh":
        payload, input_format = _load_json_or_ndjson(raw_bytes)
        return ParseResult(records=_normalize_wazuh_records(payload), input_format=input_format)

    if source == "suricata":
        payload, input_format = _load_json_or_ndjson(raw_bytes)
        if isinstance(payload, list):
            payload = {"events": payload}
        return ParseResult(records=_normalize_suricata_records(payload), input_format=input_format)

    if source == "nmap":
        text = raw_bytes.decode("utf-8", errors="ignore").lstrip()
        if filename and filename.lower().endswith(".xml") or text.startswith("<nmaprun"):
            return ParseResult(records=_normalize_nmap_records(_parse_nmap_xml(raw_bytes)), input_format="xml")
        payload, input_format = _load_json_or_ndjson(raw_bytes)
        return ParseResult(records=_normalize_nmap_records(_parse_nmap_json(payload)), input_format=input_format)

    if source == "hydra":
        text = raw_bytes.decode("utf-8", errors="ignore").lstrip()
        if filename and filename.lower().endswith(".txt"):
            return ParseResult(records=_normalize_hydra_records(_parse_hydra_text(raw_bytes)), input_format="txt")
        if text and text[0] not in "[{":
            return ParseResult(records=_normalize_hydra_records(_parse_hydra_text(raw_bytes)), input_format="txt")
        payload, input_format = _load_json_or_ndjson(raw_bytes)
        return ParseResult(records=_normalize_hydra_records(_parse_hydra_json(payload)), input_format=input_format)

    supported = ", ".join(sorted(LAB_ONLY_IMPORT_SOURCES | {"suricata", "wazuh"}))
    raise ValueError(f"Unsupported integration source: {source}. Supported sources: {supported}")
