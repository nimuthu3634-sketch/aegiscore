from __future__ import annotations

import asyncio

import anyio
from fastapi.encoders import jsonable_encoder

from app.services.mock_store import DEMO_ALERTS
from app.ws.connection_manager import ConnectionManager

alert_stream_manager = ConnectionManager()


def _latest_alert() -> dict | None:
    if not DEMO_ALERTS:
        return None

    return max(DEMO_ALERTS, key=lambda alert: alert["created_at"])


def build_alert_stream_ready_payload() -> dict:
    latest_alert = _latest_alert()
    return {
        "event": "alerts_stream_ready",
        "message": "Live alert stream connected.",
        "latest_alert": jsonable_encoder(latest_alert) if latest_alert else None,
    }


def build_alert_created_payload(alert_record: dict) -> dict:
    encoded_alert = jsonable_encoder(alert_record)
    return {
        "event": "alert_created",
        "message": f"New {encoded_alert['severity']} alert from {encoded_alert['source_tool']}.",
        "alert": encoded_alert,
    }


async def broadcast_alert_created_async(alert_record: dict) -> None:
    await alert_stream_manager.broadcast(build_alert_created_payload(alert_record))


def broadcast_alert_created(alert_record: dict) -> None:
    try:
        anyio.from_thread.run(broadcast_alert_created_async, alert_record)
        return
    except RuntimeError:
        pass

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    loop.create_task(broadcast_alert_created_async(alert_record))
