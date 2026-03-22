from copy import deepcopy

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.enums import AlertSeverity, IntegrationTool
from app.db.base import Base
from app.services import alerts as alerts_service
from app.services import incidents as incidents_service
from app.services import logs as logs_service
from app.services.dashboard import get_dashboard_summary
from app.services.mock_store import DEMO_ALERTS, DEMO_INCIDENTS, DEMO_LOGS


@pytest.fixture(autouse=True)
def restore_demo_state() -> None:
    alerts_snapshot = deepcopy(DEMO_ALERTS)
    incidents_snapshot = deepcopy(DEMO_INCIDENTS)
    logs_snapshot = deepcopy(DEMO_LOGS)

    yield

    DEMO_ALERTS[:] = alerts_snapshot
    DEMO_INCIDENTS[:] = incidents_snapshot
    DEMO_LOGS[:] = logs_snapshot


@pytest.fixture
def sqlite_storage(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'aegiscore-persistence.db'}", future=True)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def run_with_sqlite(operation, fallback):
        db = testing_session_local()
        try:
            return operation(db)
        except SQLAlchemyError:
            db.rollback()
            return fallback()
        finally:
            db.close()

    monkeypatch.setattr(alerts_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(logs_service, "run_with_optional_db", run_with_sqlite)
    monkeypatch.setattr(incidents_service, "run_with_optional_db", run_with_sqlite)


def test_alert_log_and_incident_survive_memory_reset_via_database(sqlite_storage) -> None:
    created_log = logs_service.create_log_record(
        {
            "source": "lab-db-01",
            "source_tool": IntegrationTool.WAZUH,
            "severity": "medium",
            "event_type": "authentication",
            "raw_log": {
                "timestamp": "2026-03-22T11:05:00Z",
                "host": "lab-db-01",
                "message": "Failed password for invalid user dbuser from 10.0.0.50",
                "user": "dbuser",
                "source_ip": "10.0.0.50",
            },
        }
    )

    created_alert = alerts_service.create_alert(
        title="Database-backed suspicious login burst",
        description="Alert persisted through the database-backed alert service path.",
        source="lab-db-01",
        source_tool=IntegrationTool.WAZUH,
        severity=AlertSeverity.MEDIUM,
        confidence_score=0.77,
    )

    created_incident = incidents_service.create_incident(
        alert_id=created_alert["id"],
        notes="Incident persisted through the database-backed incident workflow.",
    )

    DEMO_LOGS[:] = [log for log in DEMO_LOGS if log["id"] != created_log["id"]]
    DEMO_ALERTS[:] = [alert for alert in DEMO_ALERTS if alert["id"] != created_alert["id"]]
    DEMO_INCIDENTS[:] = [incident for incident in DEMO_INCIDENTS if incident["id"] != created_incident["id"]]

    reloaded_log = logs_service.get_log_by_id(created_log["id"])
    reloaded_alert = alerts_service.get_alert_by_id(created_alert["id"])
    reloaded_incident = incidents_service.get_incident_by_id(created_incident["id"])

    assert reloaded_log["source"] == "lab-db-01"
    assert reloaded_alert["title"] == "Database-backed suspicious login burst"
    assert reloaded_incident["alert_id"] == created_alert["id"]

    dashboard_summary = get_dashboard_summary()
    assert dashboard_summary["total_alerts"] == len(DEMO_ALERTS) + 1
    assert dashboard_summary["open_incidents"] >= 1

    next_alert = alerts_service.create_alert(
        title="Second persisted alert after reload",
        description="This verifies ID generation continues from persisted records.",
        source="lab-db-02",
        source_tool=IntegrationTool.SURICATA,
        severity=AlertSeverity.LOW,
        confidence_score=0.61,
    )

    assert next_alert["id"] != created_alert["id"]
    assert next_alert["id"] > created_alert["id"]
