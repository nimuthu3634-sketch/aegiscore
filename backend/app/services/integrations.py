from app.core.enums import IntegrationType
from app.utils.time import utc_now


def list_integrations() -> list[dict]:
    now = utc_now()
    return [
        {
            "id": "INT-01",
            "name": "Wazuh manager",
            "integration_type": IntegrationType.WAZUH,
            "is_enabled": True,
            "last_sync_at": now,
        },
        {
            "id": "INT-02",
            "name": "Suricata sensor",
            "integration_type": IntegrationType.SURICATA,
            "is_enabled": True,
            "last_sync_at": now,
        },
        {
            "id": "INT-03",
            "name": "Nmap lab importer",
            "integration_type": IntegrationType.NMAP,
            "is_enabled": False,
            "last_sync_at": now,
        },
        {
            "id": "INT-04",
            "name": "Hydra lab importer",
            "integration_type": IntegrationType.HYDRA,
            "is_enabled": False,
            "last_sync_at": now,
        },
    ]
