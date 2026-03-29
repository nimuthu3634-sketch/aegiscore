from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha1
from typing import Any

from app.models.entities import AlertSeverity, IntegrationType


SUPPORTED_INPUT_FORMATS: dict[str, list[str]] = {
    IntegrationType.WAZUH.value: ["json", "ndjson"],
    IntegrationType.SURICATA.value: ["json", "ndjson"],
    IntegrationType.NMAP.value: ["json", "xml"],
    IntegrationType.HYDRA.value: ["json", "ndjson", "txt"],
}

SYNC_CAPABLE_SOURCES = {IntegrationType.WAZUH.value, IntegrationType.SURICATA.value}
LAB_ONLY_IMPORT_SOURCES = {IntegrationType.NMAP.value, IntegrationType.HYDRA.value}


def build_fingerprint(*parts: Any) -> str:
    rendered = "|".join("" if part is None else str(part) for part in parts)
    return sha1(rendered.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class NormalizedRecord:
    title: str
    description: str | None
    source: str
    source_type: str
    event_type: str | None
    severity: AlertSeverity
    occurred_at: datetime | None
    asset_hostname: str | None
    asset_ip: str | None
    tags: list[str]
    message: str
    level: str
    category: str | None
    raw_payload: dict[str, Any]
    parsed_payload: dict[str, Any]
    incident_candidate: bool
    external_id: str | None = None
    detected_at: datetime | None = None
    fingerprint: str | None = None
    operating_system: str | None = None
    business_unit: str | None = None
    should_create_alert: bool = True
    imported_lab_data: bool = False

    def finalize(self) -> "NormalizedRecord":
        if self.imported_lab_data:
            self.parsed_payload = {
                **self.parsed_payload,
                "lab_imported": True,
                "execution_supported": False,
            }

        if not self.asset_hostname and self.asset_ip:
            self.asset_hostname = self.asset_ip.replace(":", "-")
        if not self.detected_at:
            self.detected_at = self.occurred_at

        fingerprint = self.fingerprint or build_fingerprint(
            self.source,
            self.external_id,
            self.title,
            self.asset_hostname,
            self.asset_ip,
            self.occurred_at.isoformat() if self.occurred_at else None,
            self.message,
        )
        self.fingerprint = fingerprint
        self.external_id = self.external_id or fingerprint
        self.tags = sorted({tag for tag in self.tags if tag})
        return self


@dataclass(slots=True)
class ParseResult:
    records: list[NormalizedRecord] = field(default_factory=list)
    input_format: str | None = None
