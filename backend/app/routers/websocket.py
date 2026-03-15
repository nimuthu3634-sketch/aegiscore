from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket import build_alert_stream_payload
from app.ws.connection_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/alerts")
async def alerts_websocket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    await manager.send_personal_message(build_alert_stream_payload(), websocket)

    try:
        while True:
            message = await websocket.receive_text()
            await manager.send_personal_message(
                {"event": "ack", "message": f"Received: {message}"},
                websocket,
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
