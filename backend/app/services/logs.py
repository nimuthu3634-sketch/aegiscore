from app.utils.time import utc_now


def list_logs() -> list[dict]:
    now = utc_now()
    return [
        {
            "id": "LOG-9001",
            "source": "wazuh",
            "event_type": "authentication",
            "severity": "high",
            "raw_message": "Failed password for invalid user analyst from 10.0.0.22",
            "event_time": now,
        },
        {
            "id": "LOG-9002",
            "source": "suricata",
            "event_type": "network",
            "severity": "medium",
            "raw_message": "ET POLICY Suspicious DNS request pattern observed.",
            "event_time": now,
        },
    ]
