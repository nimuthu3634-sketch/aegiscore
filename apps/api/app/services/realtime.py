from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[channel].add(websocket)

    def disconnect(self, channel: str, websocket: WebSocket) -> None:
        self.connections[channel].discard(websocket)
        if not self.connections[channel]:
            self.connections.pop(channel, None)

    async def broadcast(self, channel: str, payload: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in self.connections.get(channel, set()):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)

        for websocket in stale:
            self.disconnect(channel, websocket)


manager = RealtimeManager()
