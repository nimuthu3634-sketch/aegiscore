from __future__ import annotations

from collections import Counter
from datetime import date, datetime

from fastapi import HTTPException, encoders, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.enums import (
    AlertSeverity,
    IncidentStatus,
    IntegrationTool,
    ReportStatus,
    ReportType,
)
from app.db.init_db import init_db
from app.models.report import Report
from app.models.user import User
from app.services.anomaly import ensure_demo_alerts_scored
from app.services.alerts import load_alert_records
from app.services.incidents import load_incident_records
from app.services.mock_store import DEMO_REPORTS
from app.services.record_ids import next_prefixed_id
from app.services.users import get_user_by_id
from app.utils.time import ensure_utc, utc_now

SEVERITY_ORDER = [
    AlertSeverity.CRITICAL,
    AlertSeverity.HIGH,
    AlertSeverity.MEDIUM,
    AlertSeverity.LOW,
]
SOURCE_TOOL_ORDER = [
    IntegrationTool.WAZUH,
    IntegrationTool.SURICATA,
    IntegrationTool.NMAP,
    IntegrationTool.HYDRA,
    IntegrationTool.VIRTUALBOX,
]
INCIDENT_STATUS_ORDER = [
    IncidentStatus.OPEN,
    IncidentStatus.TRIAGED,
    IncidentStatus.IN_PROGRESS,
    IncidentStatus.RESOLVED,
]


def _enum_value(value):
    return value.value if hasattr(value, "value") else value


def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_from cannot be later than date_to.",
        )


def _within_date_range(
    value: datetime | None,
    *,
    date_from: date | None,
    date_to: date | None,
) -> bool:
    if value is None:
        return False

    value_date = value.date()
    if date_from and value_date < date_from:
        return False
    if date_to and value_date > date_to:
        return False
    return True


def _get_user_name(user_id: str | None) -> str | None:
    if not user_id:
        return None

    user_record = get_user_by_id(user_id)
    return user_record["full_name"] if user_record else None


def _serialize_report(report_record: dict) -> dict:
    return {
        **report_record,
        "generated_by_name": _get_user_name(report_record.get("generated_by_user_id")),
    }


def _report_from_model(report: Report) -> dict:
    return {
        "id": report.id,
        "title": report.title,
        "report_type": report.report_type,
        "generated_by_user_id": report.generated_by_user_id,
        "generated_by_name": _get_user_name(report.generated_by_user_id),
        "content_json": report.content_json,
        "status": report.status,
        "created_at": ensure_utc(report.created_at),
    }


def _load_persisted_reports(db: Session | None) -> list[dict]:
    if db is None:
        return []

    try:
        reports = db.scalars(select(Report).order_by(Report.created_at.desc())).all()
    except SQLAlchemyError:
        db.rollback()
        return []

    return [_report_from_model(report) for report in reports]


def _merged_report_records(db: Session | None) -> list[dict]:
    merged_records = {
        report["id"]: _serialize_report(report)
        for report in DEMO_REPORTS
    }

    for persisted_report in _load_persisted_reports(db):
        merged_records[persisted_report["id"]] = persisted_report

    return sorted(merged_records.values(), key=lambda report: report["created_at"], reverse=True)


def _filter_alerts(*, date_from: date | None, date_to: date | None) -> list[dict]:
    ensure_demo_alerts_scored()
    return [
        alert
        for alert in load_alert_records()
        if _within_date_range(alert.get("created_at"), date_from=date_from, date_to=date_to)
    ]


def _filter_incidents(*, date_from: date | None, date_to: date | None) -> list[dict]:
    return [
        incident
        for incident in load_incident_records()
        if _within_date_range(incident.get("opened_at"), date_from=date_from, date_to=date_to)
    ]


def _filter_reports(
    *,
    date_from: date | None,
    date_to: date | None,
    db: Session | None,
) -> list[dict]:
    return [
        report
        for report in _merged_report_records(db)
        if _within_date_range(report.get("created_at"), date_from=date_from, date_to=date_to)
    ]


def _count_points(records: list[dict], field_name: str, enum_order: list) -> list[dict]:
    counter = Counter(_enum_value(record.get(field_name)) for record in records)
    return [
        {
            field_name: enum_value,
            "count": counter.get(enum_value.value, 0),
        }
        for enum_value in enum_order
    ]


def _build_anomaly_summary(filtered_alerts: list[dict]) -> dict:
    ensure_demo_alerts_scored()
    from app.ml.anomaly import anomaly_detector

    metadata = anomaly_detector.get_training_metadata()
    sorted_alerts = sorted(
        filtered_alerts,
        key=lambda alert: (float(alert.get("anomaly_score", 0.0)), alert.get("created_at")),
        reverse=True,
    )
    anomaly_scores = [float(alert.get("anomaly_score", 0.0)) for alert in filtered_alerts]

    return {
        "model_name": metadata.model_name,
        "trained_on_events": metadata.trained_on_events,
        "feature_labels": metadata.feature_labels,
        "trained_at": metadata.trained_at,
        "average_anomaly_score": round(
            sum(anomaly_scores) / len(anomaly_scores),
            2,
        )
        if anomaly_scores
        else 0.0,
        "anomalous_alert_count": sum(1 for alert in filtered_alerts if alert.get("is_anomalous")),
        "high_anomaly_alert_count": sum(
            1 for alert in filtered_alerts if float(alert.get("anomaly_score", 0.0)) >= 0.7
        ),
        "top_anomalous_alerts": sorted_alerts[:5],
    }


def _build_report_summary(
    *,
    date_from: date | None,
    date_to: date | None,
    db: Session | None,
) -> dict:
    filtered_alerts = _filter_alerts(date_from=date_from, date_to=date_to)
    filtered_incidents = _filter_incidents(date_from=date_from, date_to=date_to)
    filtered_reports = _filter_reports(date_from=date_from, date_to=date_to, db=db)
    anomaly_summary = _build_anomaly_summary(filtered_alerts)

    return {
        "date_from": date_from,
        "date_to": date_to,
        "reports_generated": len(filtered_reports),
        "draft_reports": sum(1 for report in filtered_reports if report["status"] == ReportStatus.DRAFT),
        "ready_reports": sum(1 for report in filtered_reports if report["status"] == ReportStatus.READY),
        "filtered_alert_count": len(filtered_alerts),
        "filtered_incident_count": len(filtered_incidents),
        "alerts_by_severity": _count_points(filtered_alerts, "severity", SEVERITY_ORDER),
        "alerts_by_source_tool": _count_points(filtered_alerts, "source_tool", SOURCE_TOOL_ORDER),
        "incidents_by_status": _count_points(filtered_incidents, "status", INCIDENT_STATUS_ORDER),
        "anomaly_summary": anomaly_summary,
    }


def _default_report_title(
    report_type: ReportType,
    *,
    date_from: date | None,
    date_to: date | None,
) -> str:
    report_label = {
        ReportType.EXECUTIVE: "Executive summary",
        ReportType.INCIDENT: "Incident digest",
        ReportType.OPERATIONS: "Operations snapshot",
        ReportType.ANALYTICS: "Analytics overview",
    }[report_type]

    if date_from and date_to:
        return f"{report_label} ({date_from.isoformat()} to {date_to.isoformat()})"
    if date_from:
        return f"{report_label} (from {date_from.isoformat()})"
    if date_to:
        return f"{report_label} (through {date_to.isoformat()})"

    return f"{report_label} ({utc_now().date().isoformat()})"


def _build_report_content(summary: dict) -> dict:
    return encoders.jsonable_encoder(
        {
            "date_range": {
                "date_from": summary["date_from"],
                "date_to": summary["date_to"],
            },
            "summary": {
                "reports_generated": summary["reports_generated"],
                "draft_reports": summary["draft_reports"],
                "ready_reports": summary["ready_reports"],
                "filtered_alert_count": summary["filtered_alert_count"],
                "filtered_incident_count": summary["filtered_incident_count"],
                "anomalous_alert_count": summary["anomaly_summary"]["anomalous_alert_count"],
                "high_anomaly_alert_count": summary["anomaly_summary"]["high_anomaly_alert_count"],
                "average_anomaly_score": summary["anomaly_summary"]["average_anomaly_score"],
            },
            "alerts_by_severity": summary["alerts_by_severity"],
            "alerts_by_source_tool": summary["alerts_by_source_tool"],
            "incidents_by_status": summary["incidents_by_status"],
            "anomaly_summary": summary["anomaly_summary"],
        }
    )


def _persist_report_metadata(db: Session | None, report_record: dict) -> None:
    if db is None:
        return

    try:
        init_db()
        generated_by_user_id = report_record.get("generated_by_user_id")
        persisted_user_id = None

        if generated_by_user_id and db.get(User, generated_by_user_id):
            persisted_user_id = generated_by_user_id

        db.merge(
            Report(
                id=report_record["id"],
                title=report_record["title"],
                report_type=report_record["report_type"],
                generated_by_user_id=persisted_user_id,
                content_json=report_record["content_json"],
                status=report_record["status"],
                created_at=report_record["created_at"],
            )
        )
        db.commit()
    except SQLAlchemyError:
        db.rollback()


def list_reports(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session | None = None,
) -> list[dict]:
    _validate_date_range(date_from, date_to)
    return _filter_reports(date_from=date_from, date_to=date_to, db=db)


def get_reports_summary(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session | None = None,
) -> dict:
    _validate_date_range(date_from, date_to)
    return _build_report_summary(date_from=date_from, date_to=date_to, db=db)


def generate_report(
    *,
    title: str | None,
    report_type: ReportType,
    date_from: date | None,
    date_to: date | None,
    current_user: dict,
    db: Session | None = None,
) -> dict:
    _validate_date_range(date_from, date_to)
    report_record = {
        "id": next_prefixed_id("report", (report["id"] for report in _merged_report_records(db))),
        "title": title or _default_report_title(report_type, date_from=date_from, date_to=date_to),
        "report_type": report_type,
        "generated_by_user_id": current_user.get("id"),
        "content_json": {},
        "status": ReportStatus.READY,
        "created_at": utc_now(),
    }

    DEMO_REPORTS.append(report_record)
    report_record["content_json"] = _build_report_content(
        _build_report_summary(date_from=date_from, date_to=date_to, db=db)
    )
    _persist_report_metadata(db, report_record)
    return _serialize_report(report_record)
