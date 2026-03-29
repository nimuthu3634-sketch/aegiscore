from __future__ import annotations

from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
API_BASE = "http://localhost:8000/api/v1"

FILES = {
    "wazuh": DOCS / "sample-wazuh-alerts.json",
    "suricata": DOCS / "sample-suricata-events.json",
    "nmap": DOCS / "sample-nmap-results.json",
    "hydra": DOCS / "sample-hydra-results.json",
}


def login() -> str:
    response = httpx.post(
        f"{API_BASE}/auth/login",
        json={"email": "admin@example.com", "password": "Admin123!"},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> None:
    token = login()
    headers = {"Authorization": f"Bearer {token}"}

    for integration, path in FILES.items():
        if not path.exists():
            print(f"Skipping {integration}: file not found at {path}")
            continue

        with path.open("rb") as handle:
            response = httpx.post(
                f"{API_BASE}/integrations/{integration}/import",
                headers=headers,
                files={"file": (path.name, handle, "application/json")},
                timeout=60.0,
            )
            response.raise_for_status()
            print(f"Imported {integration}: {response.json()}")


if __name__ == "__main__":
    main()
