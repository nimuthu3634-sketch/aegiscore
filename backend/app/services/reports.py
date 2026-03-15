from app.core.enums import ReportStatus
from app.services.mock_store import DEMO_REPORTS


def list_reports() -> list[dict]:
    return DEMO_REPORTS


def get_reports_summary() -> dict:
    return {
        "reports_generated": len(DEMO_REPORTS),
        "draft_reports": sum(1 for report in DEMO_REPORTS if report["status"] == ReportStatus.DRAFT),
        "ready_reports": sum(1 for report in DEMO_REPORTS if report["status"] == ReportStatus.READY),
    }
