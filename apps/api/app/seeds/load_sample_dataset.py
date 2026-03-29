from __future__ import annotations

import asyncio
from pathlib import Path

from app.db.init_db import ensure_default_integrations
from app.db.session import SessionLocal
from app.models.entities import User
from app.seeds.seed_demo import run_seed
from app.services.domain import rescore_alerts
from app.services.integrations import import_integration_file


def load_sample_dataset() -> None:
    run_seed()
    base_dir = Path(__file__).resolve().parents[4]
    docs_dir = base_dir / "docs"

    db = SessionLocal()
    try:
        ensure_default_integrations(db)
        actor = db.query(User).filter(User.email == "admin@example.com").one()
        fixtures = [
            ("wazuh", docs_dir / "sample-wazuh-alerts.json"),
            ("suricata", docs_dir / "sample-suricata-events.json"),
            ("nmap", docs_dir / "sample-nmap-results.json"),
            ("hydra", docs_dir / "sample-hydra-results.json"),
        ]
        for source, path in fixtures:
            if not path.exists():
                continue
            asyncio.run(
                import_integration_file(
                    db,
                    slug=source,
                    filename=path.name,
                    raw_bytes=path.read_bytes(),
                    actor=actor,
                    ip_address="127.0.0.1",
                )
            )
        rescore_alerts(db, open_only=False)
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_dataset()
