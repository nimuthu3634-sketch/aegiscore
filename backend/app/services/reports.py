from app.core.enums import ReportStatus
from app.utils.time import utc_now


def list_reports() -> list[dict]:
    now = utc_now()
    return [
        {
            "id": "REP-01",
            "name": "Weekly SOC posture",
            "report_type": "executive_summary",
            "generated_by": "Admin",
            "status": ReportStatus.READY,
            "generated_at": now,
        },
        {
            "id": "REP-02",
            "name": "Anomaly digest",
            "report_type": "ml_summary",
            "generated_by": "Analyst",
            "status": ReportStatus.DRAFT,
            "generated_at": now,
        },
    ]
