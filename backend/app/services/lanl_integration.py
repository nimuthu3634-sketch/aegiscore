from __future__ import annotations

import csv
import gzip
import io
from collections import defaultdict
from datetime import timedelta
from typing import Any

from fastapi import HTTPException, UploadFile, status

from app.core.enums import AlertSeverity, AlertStatus, IntegrationHealth, IntegrationTool
from app.ingestion.parsers import (
    LANL_FAILURE_VALUES,
    LANL_SENSITIVE_PORTS,
    parse_lanl_auth_record,
    parse_lanl_dns_record,
    parse_lanl_flow_record,
)
from app.services.alerts import create_alert, load_alert_records
from app.services.integrations import get_latest_alert_titles_for_tool
from app.services.logs import create_log_record, load_log_records
from app.utils.time import utc_now

LANL_DATASET_TYPES = {"auth", "dns", "flows"}


def _lanl_log_records() -> list[dict]:
    return [record for record in load_log_records() if record.get("source_tool") == IntegrationTool.LANL]


def _lanl_alert_records() -> list[dict]:
    return [record for record in load_alert_records() if record.get("source_tool") == IntegrationTool.LANL]


def get_lanl_status() -> dict[str, Any]:
    log_records = _lanl_log_records()
    alert_records = _lanl_alert_records()
    timeline_records = [*log_records, *alert_records]
    last_import_at = (
        max(record["created_at"] for record in timeline_records)
        if timeline_records
        else None
    )
    imported_alert_count = len(alert_records)
    imported_log_count = len(log_records)

    return {
        "tool_name": IntegrationTool.LANL,
        "status": IntegrationHealth.CONNECTED if timeline_records else IntegrationHealth.PENDING,
        "last_sync_at": last_import_at,
        "notes": (
            "Upload official LANL Comprehensive auth.txt.gz, dns.txt.gz, or flows.txt.gz files. "
            "Optional redteam.txt.gz enrichment is supported for auth imports."
        ),
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "last_import_at": last_import_at,
        "last_import_message": (
            f"AegisCore currently holds {imported_alert_count} alerts and {imported_log_count} logs "
            "from LANL Comprehensive imports."
            if timeline_records
            else None
        ),
        "supported_dataset_types": sorted(LANL_DATASET_TYPES),
        "redteam_supported": True,
        "latest_imported_alert_titles": get_latest_alert_titles_for_tool(IntegrationTool.LANL),
    }


def _ensure_dataset_type(dataset_type: str) -> str:
    normalized_type = dataset_type.strip().lower()
    if normalized_type not in LANL_DATASET_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="dataset_type must be one of auth, dns, or flows.",
        )
    return normalized_type


def _ensure_record_limit(max_records: int) -> int:
    if max_records < 1 or max_records > 20_000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_records must be between 1 and 20000.",
        )
    return max_records


def _open_upload_text_stream(upload: UploadFile) -> io.TextIOBase:
    upload.file.seek(0)
    file_header = upload.file.read(2)
    upload.file.seek(0)

    if file_header == b"\x1f\x8b" or (upload.filename or "").lower().endswith(".gz"):
        return io.TextIOWrapper(gzip.GzipFile(fileobj=upload.file, mode="rb"), encoding="utf-8")

    return io.TextIOWrapper(upload.file, encoding="utf-8")


def _read_redteam_matches(redteam_file: UploadFile | None) -> set[tuple[str, str, str, str]]:
    if redteam_file is None:
        return set()

    matches: set[tuple[str, str, str, str]] = set()
    text_stream = _open_upload_text_stream(redteam_file)

    try:
        for row in csv.reader(text_stream):
            if len(row) < 4:
                continue

            relative_time = row[0].strip()
            username = row[1].strip().lower()
            username_short = username.split("@", 1)[0]
            source_computer = row[2].strip().lower()
            destination_computer = row[3].strip().lower()

            matches.add((relative_time, username, source_computer, destination_computer))
            matches.add((relative_time, username_short, source_computer, destination_computer))
    finally:
        text_stream.close()

    return matches


def _is_redteam_auth_match(row: list[str], redteam_matches: set[tuple[str, str, str, str]]) -> bool:
    if len(row) < 5:
        return False

    relative_time = row[0].strip()
    username = row[1].strip().lower()
    username_short = username.split("@", 1)[0]
    source_computer = row[3].strip().lower()
    destination_computer = row[4].strip().lower()

    return (
        (relative_time, username, source_computer, destination_computer) in redteam_matches
        or (relative_time, username_short, source_computer, destination_computer) in redteam_matches
    )


def _existing_lanl_references() -> set[str]:
    return {
        record["integration_ref"]
        for record in _lanl_log_records()
        if record.get("integration_ref")
    }


def _lanl_reference(dataset_type: str, metadata: dict[str, Any]) -> str:
    if dataset_type == "auth":
        return ":".join(
            [
                "lanl",
                "auth",
                str(metadata.get("relative_time_seconds")),
                str(metadata.get("source_user") or "unknown-user"),
                str(metadata.get("source_computer") or "unknown-source"),
                str(metadata.get("destination_computer") or "unknown-target"),
                str(metadata.get("auth_outcome") or "unknown-outcome"),
            ]
        )

    if dataset_type == "dns":
        return ":".join(
            [
                "lanl",
                "dns",
                str(metadata.get("relative_time_seconds")),
                str(metadata.get("source_computer") or "unknown-source"),
                str(metadata.get("resolved_name") or "unknown-destination"),
            ]
        )

    return ":".join(
        [
            "lanl",
            "flows",
            str(metadata.get("relative_time_seconds")),
            str(metadata.get("source_computer") or "unknown-source"),
            str(metadata.get("destination_computer") or "unknown-target"),
            str(metadata.get("destination_port") or "unknown-port"),
            str(metadata.get("protocol") or "unknown-protocol"),
        ]
    )


def _iter_parsed_lanl_records(
    dataset_type: str,
    dataset_file: UploadFile,
    *,
    redteam_matches: set[tuple[str, str, str, str]],
    max_records: int,
    existing_references: set[str],
) -> tuple[list[dict[str, Any]], int]:
    parsed_records: list[dict[str, Any]] = []
    skipped_count = 0
    text_stream = _open_upload_text_stream(dataset_file)

    try:
        for row in csv.reader(text_stream):
            if not row or not any(cell.strip() for cell in row):
                continue

            try:
                if dataset_type == "auth":
                    parsed_record = parse_lanl_auth_record(
                        row,
                        redteam_match=_is_redteam_auth_match(row, redteam_matches),
                    )
                elif dataset_type == "dns":
                    parsed_record = parse_lanl_dns_record(row)
                else:
                    parsed_record = parse_lanl_flow_record(row)
            except (TypeError, ValueError):
                skipped_count += 1
                continue

            integration_ref = _lanl_reference(
                dataset_type,
                parsed_record["finding_metadata"],
            )
            if integration_ref in existing_references:
                skipped_count += 1
                continue

            existing_references.add(integration_ref)
            parsed_record["integration_ref"] = integration_ref
            parsed_records.append(parsed_record)

            if len(parsed_records) >= max_records:
                break
    finally:
        text_stream.close()

    return parsed_records, skipped_count


def _anchor_lanl_timeline(parsed_records: list[dict[str, Any]], import_time) -> None:
    if not parsed_records:
        return

    latest_relative_time = max(
        int(record["relative_time_seconds"])
        for record in parsed_records
    )
    for record in parsed_records:
        relative_time_seconds = int(record["relative_time_seconds"])
        record["created_at"] = import_time - timedelta(
            seconds=latest_relative_time - relative_time_seconds
        )
        record["finding_metadata"] = {
            **record["finding_metadata"],
            "timeline_anchor": "relative_time_order_preserved_at_import",
            "anchored_created_at": record["created_at"].isoformat(),
        }


def _persist_lanl_logs(parsed_records: list[dict[str, Any]]) -> int:
    imported_log_count = 0

    for record in parsed_records:
        create_log_record(
            {
                "source": record["source"],
                "source_tool": IntegrationTool.LANL.value,
                "timestamp": record["created_at"],
                "severity": record["severity"].value,
                "event_type": record["event_type"],
                "raw_log": {
                    **record["raw_event"],
                    "message": record["message"],
                },
            },
            extra_fields={
                "integration_ref": record["integration_ref"],
                "finding_metadata": record["finding_metadata"],
                "parser_status": record.get("parser_status"),
                "lab_only": False,
            },
        )
        imported_log_count += 1

    return imported_log_count


def _create_lanl_alert(
    *,
    title: str,
    description: str,
    source: str,
    severity: AlertSeverity,
    created_at,
    integration_ref: str,
    event_type: str,
    finding_metadata: dict[str, Any],
    confidence_score: float,
) -> None:
    create_alert(
        title=title,
        description=description,
        source=source,
        source_tool=IntegrationTool.LANL.value,
        severity=severity,
        status_value=AlertStatus.NEW,
        confidence_score=confidence_score,
        created_at=created_at,
        extra_fields={
            "integration_ref": integration_ref,
            "finding_metadata": {
                **finding_metadata,
                "event_type": event_type,
            },
            "parser_status": "normalized",
            "lab_only": False,
        },
    )


def _create_auth_alerts(parsed_records: list[dict[str, Any]]) -> tuple[int, int]:
    redteam_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    failure_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for record in parsed_records:
        metadata = record["finding_metadata"]
        key = (
            str(metadata.get("source_user") or "unknown-user"),
            str(metadata.get("source_computer") or record["source"]),
            str(metadata.get("destination_computer") or "unknown-target"),
        )

        if metadata.get("redteam_match"):
            redteam_groups[key].append(record)
        elif str(metadata.get("auth_outcome") or "").strip().lower() in LANL_FAILURE_VALUES:
            failure_groups[key].append(record)

    imported_alert_count = 0
    redteam_match_count = sum(len(group) for group in redteam_groups.values())

    for (source_user, source_computer, destination_computer), records in redteam_groups.items():
        latest_record = max(records, key=lambda item: item["created_at"])
        _create_lanl_alert(
            title="Known compromise path observed in LANL auth data",
            description=(
                f"{len(records)} authentication events for {source_user} from {source_computer} "
                f"to {destination_computer} matched the LANL red-team ground truth."
            ),
            source=source_computer,
            severity=AlertSeverity.CRITICAL,
            created_at=latest_record["created_at"],
            integration_ref=(
                f"lanl:auth:redteam:{source_user}:{source_computer}:{destination_computer}:"
                f"{latest_record['finding_metadata']['relative_time_seconds']}"
            ),
            event_type="compromise",
            finding_metadata={
                "dataset_source": "lanl_comprehensive",
                "dataset_type": "auth",
                "source_user": source_user,
                "source_computer": source_computer,
                "destination_computer": destination_computer,
                "matched_event_count": len(records),
                "redteam_match": True,
                "relative_time_seconds": latest_record["finding_metadata"]["relative_time_seconds"],
            },
            confidence_score=0.98,
        )
        imported_alert_count += 1

    for (source_user, source_computer, destination_computer), records in failure_groups.items():
        if len(records) < 3:
            continue

        latest_record = max(records, key=lambda item: item["created_at"])
        severity = AlertSeverity.CRITICAL if len(records) >= 10 else AlertSeverity.HIGH
        _create_lanl_alert(
            title="Repeated failed authentication activity in LANL data",
            description=(
                f"{len(records)} failed authentication events were imported for {source_user} "
                f"from {source_computer} to {destination_computer}."
            ),
            source=source_computer,
            severity=severity,
            created_at=latest_record["created_at"],
            integration_ref=(
                f"lanl:auth:failures:{source_user}:{source_computer}:{destination_computer}:"
                f"{latest_record['finding_metadata']['relative_time_seconds']}"
            ),
            event_type="authentication",
            finding_metadata={
                "dataset_source": "lanl_comprehensive",
                "dataset_type": "auth",
                "source_user": source_user,
                "source_computer": source_computer,
                "destination_computer": destination_computer,
                "failed_event_count": len(records),
                "relative_time_seconds": latest_record["finding_metadata"]["relative_time_seconds"],
            },
            confidence_score=0.86 if severity == AlertSeverity.CRITICAL else 0.79,
        )
        imported_alert_count += 1

    return imported_alert_count, redteam_match_count


def _create_dns_alerts(parsed_records: list[dict[str, Any]]) -> int:
    grouped_records: dict[str, dict[str, Any]] = {}

    for record in parsed_records:
        source = record["source"]
        metadata = record["finding_metadata"]
        group = grouped_records.setdefault(
            source,
            {
                "count": 0,
                "destinations": set(),
                "latest_record": record,
            },
        )
        group["count"] += 1
        group["destinations"].add(str(metadata.get("resolved_name") or "unknown-destination"))
        if record["created_at"] > group["latest_record"]["created_at"]:
            group["latest_record"] = record

    imported_alert_count = 0
    ranked_groups = sorted(
        grouped_records.items(),
        key=lambda item: (item[1]["count"], len(item[1]["destinations"])),
        reverse=True,
    )

    for source, group in ranked_groups[:10]:
        if group["count"] < 25 and len(group["destinations"]) < 15:
            continue

        latest_record = group["latest_record"]
        severity = AlertSeverity.HIGH if group["count"] >= 50 or len(group["destinations"]) >= 25 else AlertSeverity.MEDIUM
        _create_lanl_alert(
            title="High DNS query volume in LANL dataset",
            description=(
                f"{source} resolved {len(group['destinations'])} unique destinations across "
                f"{group['count']} imported DNS events."
            ),
            source=source,
            severity=severity,
            created_at=latest_record["created_at"],
            integration_ref=(
                f"lanl:dns:volume:{source}:{latest_record['finding_metadata']['relative_time_seconds']}:"
                f"{group['count']}"
            ),
            event_type="dns_resolution",
            finding_metadata={
                "dataset_source": "lanl_comprehensive",
                "dataset_type": "dns",
                "query_count": group["count"],
                "unique_destinations": len(group["destinations"]),
                "sample_destinations": sorted(group["destinations"])[:5],
                "relative_time_seconds": latest_record["finding_metadata"]["relative_time_seconds"],
            },
            confidence_score=0.76 if severity == AlertSeverity.HIGH else 0.69,
        )
        imported_alert_count += 1

    return imported_alert_count


def _create_flow_alerts(parsed_records: list[dict[str, Any]]) -> int:
    grouped_records: dict[tuple[str, str, str], dict[str, Any]] = {}

    for record in parsed_records:
        metadata = record["finding_metadata"]
        key = (
            str(metadata.get("source_computer") or record["source"]),
            str(metadata.get("destination_computer") or "unknown-target"),
            str(metadata.get("destination_port") or "unknown-port"),
        )
        group = grouped_records.setdefault(
            key,
            {
                "count": 0,
                "total_bytes": 0,
                "max_duration": 0,
                "protocol": str(metadata.get("protocol") or "unknown"),
                "latest_record": record,
                "sensitive_port_match": bool(metadata.get("sensitive_port_match", False)),
            },
        )
        group["count"] += 1
        group["total_bytes"] += int(metadata.get("byte_count") or 0)
        group["max_duration"] = max(group["max_duration"], int(metadata.get("duration_seconds") or 0))
        group["sensitive_port_match"] = (
            group["sensitive_port_match"]
            or bool(metadata.get("sensitive_port_match", False))
            or (
                str(metadata.get("destination_port") or "").isdigit()
                and int(str(metadata.get("destination_port"))) in LANL_SENSITIVE_PORTS
            )
        )
        if record["created_at"] > group["latest_record"]["created_at"]:
            group["latest_record"] = record

    imported_alert_count = 0
    ranked_groups = sorted(
        grouped_records.items(),
        key=lambda item: (
            item[1]["sensitive_port_match"],
            item[1]["total_bytes"],
            item[1]["count"],
            item[1]["max_duration"],
        ),
        reverse=True,
    )

    for (source_computer, destination_computer, destination_port), group in ranked_groups[:15]:
        if (
            not group["sensitive_port_match"]
            and group["count"] < 5
            and group["total_bytes"] < 10_000_000
            and group["max_duration"] < 3600
        ):
            continue

        latest_record = group["latest_record"]
        severity = (
            AlertSeverity.CRITICAL
            if group["sensitive_port_match"] and group["count"] >= 5
            else AlertSeverity.HIGH
            if group["sensitive_port_match"] or group["total_bytes"] >= 10_000_000 or group["max_duration"] >= 3600
            else AlertSeverity.MEDIUM
        )
        _create_lanl_alert(
            title="Sensitive network flow pattern in LANL data",
            description=(
                f"{source_computer} communicated with {destination_computer}:{destination_port} "
                f"{group['count']} times using {group['protocol'].upper()} with {group['total_bytes']} total bytes."
            ),
            source=source_computer,
            severity=severity,
            created_at=latest_record["created_at"],
            integration_ref=(
                f"lanl:flows:pattern:{source_computer}:{destination_computer}:{destination_port}:"
                f"{latest_record['finding_metadata']['relative_time_seconds']}"
            ),
            event_type="network_flow",
            finding_metadata={
                "dataset_source": "lanl_comprehensive",
                "dataset_type": "flows",
                "source_computer": source_computer,
                "destination_computer": destination_computer,
                "destination_port": destination_port,
                "protocol": group["protocol"],
                "event_count": group["count"],
                "total_bytes": group["total_bytes"],
                "max_duration_seconds": group["max_duration"],
                "sensitive_port_match": group["sensitive_port_match"],
                "relative_time_seconds": latest_record["finding_metadata"]["relative_time_seconds"],
            },
            confidence_score=0.9 if severity == AlertSeverity.CRITICAL else 0.82 if severity == AlertSeverity.HIGH else 0.68,
        )
        imported_alert_count += 1

    return imported_alert_count


def _create_lanl_alerts(dataset_type: str, parsed_records: list[dict[str, Any]]) -> tuple[int, int]:
    if dataset_type == "auth":
        return _create_auth_alerts(parsed_records)
    if dataset_type == "dns":
        return _create_dns_alerts(parsed_records), 0
    return _create_flow_alerts(parsed_records), 0


def import_lanl_dataset_file(
    dataset_type: str,
    dataset_file: UploadFile,
    *,
    redteam_file: UploadFile | None = None,
    max_records: int = 1000,
) -> dict[str, Any]:
    normalized_type = _ensure_dataset_type(dataset_type)
    record_limit = _ensure_record_limit(max_records)
    existing_references = _existing_lanl_references()
    redteam_matches = _read_redteam_matches(redteam_file) if normalized_type == "auth" else set()

    parsed_records, skipped_count = _iter_parsed_lanl_records(
        normalized_type,
        dataset_file,
        redteam_matches=redteam_matches,
        max_records=record_limit,
        existing_references=existing_references,
    )

    last_import_at = utc_now()
    if not parsed_records:
        return {
            "dataset_type": normalized_type,
            "processed_record_count": 0,
            "imported_alert_count": 0,
            "imported_log_count": 0,
            "skipped_count": skipped_count,
            "redteam_match_count": 0,
            "last_import_at": last_import_at,
            "message": "No new LANL records were imported.",
        }

    _anchor_lanl_timeline(parsed_records, last_import_at)
    imported_log_count = _persist_lanl_logs(parsed_records)
    imported_alert_count, redteam_match_count = _create_lanl_alerts(normalized_type, parsed_records)

    return {
        "dataset_type": normalized_type,
        "processed_record_count": len(parsed_records),
        "imported_alert_count": imported_alert_count,
        "imported_log_count": imported_log_count,
        "skipped_count": skipped_count,
        "redteam_match_count": redteam_match_count,
        "last_import_at": last_import_at,
        "message": (
            f"Imported {imported_log_count} LANL {normalized_type} records and generated "
            f"{imported_alert_count} alerts."
        ),
    }
