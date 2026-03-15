from app.core.enums import AlertSeverity, AlertStatus
from app.utils.time import utc_now


def list_alerts() -> list[dict]:
    now = utc_now()
    return [
        {
            "id": "ALT-1001",
            "title": "Multiple failed SSH logins",
            "source": "Wazuh",
            "severity": AlertSeverity.HIGH,
            "status": AlertStatus.NEW,
            "summary": "Repeated failed SSH attempts from a lab workstation.",
            "occurred_at": now,
        },
        {
            "id": "ALT-1002",
            "title": "Unusual DNS query volume",
            "source": "Suricata",
            "severity": AlertSeverity.MEDIUM,
            "status": AlertStatus.TRIAGED,
            "summary": "Suricata observed a burst of DNS requests for validation.",
            "occurred_at": now,
        },
    ]
