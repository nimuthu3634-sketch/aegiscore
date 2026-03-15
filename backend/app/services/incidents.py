from app.core.enums import AlertSeverity, IncidentStatus


def list_incidents() -> list[dict]:
    return [
        {
            "id": "INC-201",
            "title": "Credential attack rehearsal review",
            "description": "Follow-up task for lab-only Hydra import validation.",
            "owner_name": "Analyst Team",
            "status": IncidentStatus.IN_PROGRESS,
            "priority": AlertSeverity.HIGH,
        },
        {
            "id": "INC-202",
            "title": "Network anomaly validation",
            "description": "Investigate spike in traffic identified by Suricata.",
            "owner_name": "Blue Lab",
            "status": IncidentStatus.TRIAGED,
            "priority": AlertSeverity.MEDIUM,
        },
    ]
